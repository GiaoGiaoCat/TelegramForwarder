# Telegram Forwarder - Architecture Overview

**Project Purpose**: A sophisticated Telegram message forwarding system with AI processing, RSS generation, and multi-platform push notifications.

## Core Architecture

### Main Entry Point & Client Initialization

**Location**: `main.py`

The application uses **two independent Telethon clients**:
- **User Client** (`./sessions/user`): Monitors messages in source chats/channels owned by the user
- **Bot Client** (`./sessions/bot`): Receives commands and executes message forwarding via bot token

**Key Lifecycle**:
1. Database initialization via SQLAlchemy (`models.init_db()`)
2. Both clients start asynchronously
3. Message listeners are registered (`setup_listeners()`)
4. Bot commands are registered via Telethon API
5. **SummaryScheduler** starts (handles scheduled AI summaries)
6. **ChatUpdater** starts (refreshes chat names in database)
7. Optional: **RSS server** starts in separate process (FastAPI-based)

**Global State**:
- `db_ops`: DBOperations singleton (initialized once, manages DB + UFB client)
- `scheduler`: SummaryScheduler instance for timed AI summaries
- `chat_updater`: ChatUpdater instance for background chat metadata updates

---

## Message Flow & Filter Chain Pattern

### Entry Point: Message Listener

**Location**: `message_listener.py`

When a message arrives at the user client:
1. **not_from_bot** filter excludes the bot's own messages (avoids recursion)
2. Routes to `handle_user_message()` for forwarding logic
3. Checks source chat has forwarding rules in database
4. Invokes `process_forward_rule()` from `filters/process.py`

**State Management**:
- Uses `StateManager` (singleton in `managers/state_manager.py`)
- Tracks user input states for multi-step command interactions
- Key: `(user_id, chat_id)` tuple → `(state_string, message_object, state_type)`

### Filter Chain: The Core Processing Pipeline

**Location**: `filters/filter_chain.py` + `filters/process.py`

**Pattern**: Chain of Responsibility
- `FilterChain` class orchestrates sequential filter execution
- Shared context (`MessageContext`) flows through all filters
- If any filter returns `False`, chain halts and message is dropped
- Errors in filters terminate the chain with status `False`

**Execution Order** (from `process_forward_rule()`):
```
1. InitFilter              → Initializes media group tracking
2. DelayFilter             → Applies optional message delay
3. KeywordFilter           → Checks whitelist/blacklist keywords (HALT if no match)
4. ReplaceFilter           → Applies text replacements
5. LinkFilter              → Removes/processes links
6. MediaFilter             → Downloads/filters media files
7. AIFilter                → Processes message via AI
8. InfoFilter              → Adds sender/time/link metadata
9. CommentButtonFilter     → Adds comment section buttons
10. RSSFilter              → Archives to RSS feed
11. EditFilter             → Edits original message if needed
12. SenderFilter           → Actually sends the message
13. ReplyFilter            → Handles media group comment buttons
14. PushFilter             → Sends to push providers (Apprise)
15. DeleteOriginalFilter   → Deletes original source message if enabled
```

**Context Object** (`MessageContext`):
```python
{
    client, event, chat_id, rule,          # Core references
    original_message_text, message_text,   # Text variants
    media_files, media_metadata,           # Media tracking
    sender_info, time_info, original_link, # Metadata fields
    buttons, should_forward,               # Control flags
    is_media_group, media_group_id,        # Group tracking
    forwarded_messages, comment_link,      # Results
    errors                                 # Error tracking
}
```

---

## Database Layer

### SQLAlchemy Models

**Location**: `models/models.py`

**Core Entities**:

1. **Chat** - Telegram chats/channels
   - `telegram_chat_id`: Unique identifier (can have -100 prefix for channels)
   - `name`: Display name
   - `current_add_id`: Selected source for current operations
   - Relationships: `source_rules`, `target_rules` (bidirectional)

2. **ForwardRule** - Message forwarding specifications
   - **Mode Settings**: 
     - `forward_mode`: WHITELIST/BLACKLIST (keyword filtering mode)
     - `add_mode`: WHITELIST/BLACKLIST (keyword add mode)
     - `handle_mode`: FORWARD/EDIT (send method)
   - **Formatting**: 
     - `message_mode`: MARKDOWN/HTML parsing
     - `is_preview`: ON/OFF/FOLLOW (link preview)
     - User/time/link templates for metadata
   - **Features**:
     - Media filters (type, size, extensions)
     - AI processing (model, prompt, image upload)
     - AI summaries (time, prompt, pin option)
     - RSS feed generation
     - Push notifications
     - Delay processing
     - UFB integration (universal forum blocker sync)
   - `enable_rule`: Master on/off flag

3. **Keyword** - Filtering keywords
   - `is_regex`: Regex vs literal matching
   - `is_blacklist`: Blacklist vs whitelist

4. **ReplaceRule** - Text replacements (pattern → content)

5. **MediaTypes** - Per-rule media type filters (photo, document, video, audio, voice)

6. **MediaExtensions** - File extension filtering (e.g., pdf, jpg)

7. **RSSConfig** - RSS feed metadata per rule

8. **User** - RSS API users (authentication)

9. **PushConfig** - Push notification settings (Apprise)

10. **RuleSync** - UFB server synchronization config

### DBOperations Manager

**Location**: `models/db_operations.py`

**Responsibilities**:
- Async database session factory
- UFB client initialization & synchronization
- Configuration syncing to UFB server

**UFB (Universal Forum Blocker)**: Optional integration for syncing keyword filters to a centralized server

---

## Handler System: Command Processing

**Location**: `handlers/`

### Bot Command Dispatcher

**File**: `handlers/bot_handler.py`

Routes incoming commands to appropriate handlers:
- `handle_command()`: Entry point, validates admin, dispatches by command name
- `callback_handler()`: Routes inline button callbacks to callback handlers

**50+ Supported Commands**:
- Binding: `/bind`, `/switch`
- Keywords: `/add`, `/add_regex`, `/list_keyword`, `/remove_keyword`
- Replacements: `/replace`, `/list_replace`, `/remove_replace`
- Rules: `/list_rule`, `/delete_rule`, `/copy_rule`
- Import/Export: `/import_keyword`, `/export_keyword`, etc.
- AI/RSS: `/list_summary`, `/delete_rss_user`, etc.
- Special: `/start`, `/help`, `/changelog`

### Command Handlers

**File**: `handlers/command_handlers.py` (~93 KB)

Implements all command logic:
- Database CRUD operations
- Message formatting (inline keyboards, text formatting)
- Interactive dialogs via StateManager
- Input validation

### Callback Handlers

**Location**: `handlers/button/callback/callback_handlers.py`

Handles inline button interactions (pagination, multi-choice selections, confirmation dialogs)

### Other Handlers

- `user_handler.py`: User account-based message forwarding
- `prompt_handlers.py`: Multi-step prompts for complex inputs
- `link_handlers.py`: Special link/URL forwarding

---

## AI Processing System

**Location**: `ai/`

### Provider Architecture

**Base Class**: `ai/base.py`

```python
class BaseAIProvider(ABC):
    async def process_message(message, prompt, images) -> str
    async def initialize() -> None
```

**Implementations**:
- `openai_provider.py`: OpenAI API + compatible services
- `gemini_provider.py`: Google Gemini
- `deepseek_provider.py`: DeepSeek
- `qwen_provider.py`: Alibaba Qwen
- `grok_provider.py`: Grok (X.AI)
- `claude_provider.py`: Anthropic Claude

### Provider Instantiation

**File**: `ai/__init__.py`

`get_ai_provider(model)` function:
1. Loads model configs from `utils/settings.py` (from environment)
2. Routes to appropriate provider class
3. Returns provider instance

### AI Filter Integration

**File**: `filters/ai_filter.py`

- **Text Processing**: Applies prompt to message text
- **Image Processing**: Base64 encodes images, sends to provider
- **Re-filtering**: Optional keyword filtering after AI processing
- Falls back if AI disabled (`rule.is_ai = False`)

---

## Scheduled Tasks

**Location**: `scheduler/`

### Summary Scheduler

**File**: `scheduler/summary_scheduler.py`

Generates time-based AI summaries of forwarded messages:
- **Trigger**: Specified time daily (e.g., 07:00)
- **Timezone**: Configurable via `DEFAULT_TIMEZONE`
- **Process**:
  1. Query messages forwarded in past 24 hours
  2. Batch fetch with configurable delay to avoid rate limits
  3. Generate AI summary via provider
  4. Split long summaries (Telegram 4096 char limit) into parts
  5. Send summary to target chat (optionally pinned)

**Config**:
- `SUMMARY_BATCH_SIZE`: Messages per batch (default 20)
- `SUMMARY_BATCH_DELAY`: Delay between batches in seconds (default 2)
- Parallel execution limited by semaphore (max 2 concurrent)

### Chat Updater

**File**: `scheduler/chat_updater.py`

Background task that:
- Runs at configured time (default 03:00)
- Fetches participant info from source chats
- Updates chat names in database
- Handles admin detection for UI rendering

---

## RSS Generation System

**Location**: `rss/` → FastAPI application in separate process

### Architecture

**Main Server**: `rss/main.py`
- FastAPI application
- Runs in `multiprocessing.Process` if `RSS_ENABLED=true`
- Separate from main async event loop

### API Structure

**Endpoints**:
- Auth routes: User login/registration
- RSS routes: Feed management UI
- Feed endpoint: `/api/feed/{rule_id}` → RSS XML

### Media Handling

RSS feeds reference media files via HTTP URLs:
- Base directory: `RSS_MEDIA_DIR` (configured in constants)
- Per-rule structure: `./rss_media/{rule_id}/` 
- Served via static file routes

### RSS Filter Integration

**File**: `filters/rss_filter.py`

During message forwarding:
1. If `RSS_ENABLED` and rule has RSS config
2. Copy media files to RSS storage directory
3. Register in RSS database with metadata
4. RSS feed XML is generated dynamically from database

---

## Configuration System

### Environment Variables

**Location**: `.env.example`

**Categories**:

1. **Required (Telegram)**:
   - `API_ID`, `API_HASH`: From my.telegram.org
   - `PHONE_NUMBER`: User account phone
   - `BOT_TOKEN`: Bot token
   - `USER_ID`: User's Telegram ID

2. **Database**:
   - `DATABASE_URL`: SQLAlchemy connection string (default SQLite)

3. **AI Providers**:
   - `{OPENAI,CLAUDE,GEMINI,DEEPSEEK,QWEN,GROK}_API_KEY`
   - `{PROVIDER}_API_BASE`: Optional custom endpoints
   - `DEFAULT_AI_MODEL`: Default model for summaries/processing
   - `DEFAULT_AI_PROMPT`, `DEFAULT_SUMMARY_PROMPT`
   - `DEFAULT_SUMMARY_TIME`: Daily summary time (HH:MM)

4. **Features**:
   - `RSS_ENABLED`: Enable RSS feed generation
   - `UFB_ENABLED`: Enable forum blocker sync

5. **Limits & Timeouts**:
   - `DEFAULT_MAX_MEDIA_SIZE`: Media size limit (MB)
   - `BOT_MESSAGE_DELETE_TIMEOUT`: Auto-delete timeout (seconds)

### Settings Loader

**File**: `utils/settings.py`

Loads AI model configurations from environment and caches them

---

## Key Architectural Patterns

### 1. **Filter Chain (Chain of Responsibility)**
   - Decoupled processing stages
   - Shared context flows through pipeline
   - Early termination on failures

### 2. **Async/Await Throughout**
   - All Telethon operations are async
   - Database operations wrapped in async context
   - Concurrent task execution via asyncio

### 3. **Global Singletons**
   - `state_manager`: User state tracking
   - `db_ops`: Database + UFB operations
   - AI providers: Instantiated per request (configurable)

### 4. **Provider Pattern (AI)**
   - Abstract base defines interface
   - Concrete providers for each API
   - Factory pattern for instantiation

### 5. **Multi-Client Strategy**
   - User client: Passive listening, flexible permissions
   - Bot client: Active sending, restricted permissions
   - Separation of concerns

### 6. **Database Relationships**
   - Bidirectional Chat ↔ ForwardRule
   - Cascade deletes: Rule deletion removes dependent configs
   - Unique constraints: Prevent duplicate rules per chat pair

---

## Important Files Reference

| Path | Purpose |
|------|---------|
| `main.py` | Entry point, client initialization |
| `message_listener.py` | Message event handlers |
| `filters/filter_chain.py` | Filter orchestration |
| `filters/process.py` | Pipeline construction |
| `filters/*.py` | Individual filter implementations |
| `filters/context.py` | Shared message context |
| `models/models.py` | SQLAlchemy ORM models |
| `models/db_operations.py` | Database abstractions |
| `handlers/bot_handler.py` | Command dispatcher |
| `handlers/command_handlers.py` | Command implementations |
| `managers/state_manager.py` | User state tracking |
| `ai/__init__.py` | AI provider factory |
| `ai/base.py` | AI provider interface |
| `ai/*_provider.py` | Provider implementations |
| `scheduler/summary_scheduler.py` | Scheduled summaries |
| `rss/main.py` | RSS FastAPI server |
| `filters/rss_filter.py` | RSS integration in pipeline |
| `utils/common.py` | Common utilities (keyword checking, etc.) |
| `enums/enums.py` | Enum types (ForwardMode, PreviewMode, etc.) |

---

## Development Notes

### Adding a New Filter

1. Create `filters/new_filter.py`
2. Extend `BaseFilter` class
3. Implement `async def _process(self, context) -> bool:`
4. Add to filter chain in `filters/process.py`
5. Update context object if needed

### Adding a New AI Provider

1. Create `ai/new_provider.py`
2. Extend `BaseAIProvider`
3. Implement required async methods
4. Register in `ai/__init__.py` factory
5. Add config to `.env.example`

### Database Changes

1. Modify SQLAlchemy model in `models/models.py`
2. Run migrations (if using Alembic) or drop/recreate DB
3. Update DBOperations methods as needed

### Common Gotchas

- **Chat ID Formats**: Telegram uses different formats (-100 prefix for supergroups, plain negative for groups, positive for chats)
- **Media Group Deduplication**: `PROCESSED_GROUPS` set prevents duplicate processing
- **Message Length Limits**: Telegram 4096 char limit; splitting handled in `SummaryScheduler`
- **Rate Limiting**: Batch delays in summary generation respect API limits
- **UFB Sync**: Requires external UFB server; gracefully fails if unavailable

