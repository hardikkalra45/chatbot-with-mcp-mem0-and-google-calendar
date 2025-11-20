# app.py
import streamlit as st
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sys
import os

# Add the current directory to path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your existing modules
try:
    from mcp_calendar_client import (
        authenticate_calendar,
        get_todays_events,
        get_weekly_events,
        get_events_for_date,
        get_upcoming_events,
        search_events,
        check_availability,
        get_next_free_slot,
        get_calendar_status,
        DateInput,
        SearchEventsInput,
        TimeSlotInput,
        DurationInput
    )
    from mem0_manager import MemoryManager
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    st.info("Make sure all required files are in the same directory")

def initialize_session_state():
    """Initialize session state variables"""
    if 'memory_manager' not in st.session_state:
        try:
            st.session_state.memory_manager = MemoryManager()
            st.session_state.memory_available = True
        except Exception as e:
            st.session_state.memory_available = False
            st.session_state.memory_error = str(e)
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'calendar_authenticated' not in st.session_state:
        st.session_state.calendar_authenticated = False
    
    if 'user_info' not in st.session_state:
        st.session_state.user_info = {}
    
    if 'user_id' not in st.session_state:
        st.session_state.user_id = "student_001"

def authenticate_calendar_service():
    """Authenticate with Google Calendar"""
    try:
        result = authenticate_calendar()
        if result.get('status') == 'success':
            st.session_state.calendar_authenticated = True
            return True
        else:
            st.error(f"Authentication failed: {result.get('message', 'Unknown error')}")
            return False
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return False

def process_calendar_query(user_input: str) -> str:
    """Process calendar-related queries with strict pattern matching"""
    user_input_lower = user_input.lower().strip()
    
    try:
        # Strict pattern matching for calendar queries
        if any(word in user_input_lower for word in ['today', "today's", 'todays']):
            result = get_todays_events()
            events = result.get('formatted_output', 'No events found for today')
            return f"📅 **Today's Schedule:**\n\n{events}"
        
        elif any(word in user_input_lower for word in ['week', 'weekly', 'this week']):
            result = get_weekly_events()
            events = result.get('formatted_output', 'No events found for this week')
            return f"📅 **Weekly Schedule:**\n\n{events}"
        
        elif any(word in user_input_lower for word in ['upcoming', 'next events', 'future events']):
            result = get_upcoming_events()
            events = result.get('formatted_output', 'No upcoming events found')
            return f"📅 **Upcoming Events:**\n\n{events}"
        
        elif user_input_lower.startswith('search ') or user_input_lower.startswith('find '):
            query = user_input_lower.replace('search', '').replace('find', '').strip()
            if query:
                search_input = SearchEventsInput(query=query, max_results=10)
                result = search_events(search_input)
                events = result.get('formatted_output', f'No events found for "{query}"')
                return f"🔍 **Search Results for '{query}':**\n\n{events}"
            else:
                return "❌ Please specify what you want to search for in your calendar."
        
        elif any(word in user_input_lower for word in ['available', 'free', 'busy']):
            if 'next' in user_input_lower and 'free' in user_input_lower:
                duration_input = DurationInput(duration_minutes=60)
                result = get_next_free_slot(duration_input)
                return f"⏰ **Availability:**\n\n{result.get('message', 'Unable to find free slot')}"
            else:
                # Check availability for next 2 hours
                start_time = datetime.now()
                end_time = start_time + timedelta(hours=2)
                time_input = TimeSlotInput(
                    start_time=start_time.isoformat(),
                    end_time=end_time.isoformat()
                )
                result = check_availability(time_input)
                if result.get('available'):
                    return "✅ **Availability:** You're available for the next 2 hours!"
                else:
                    return "❌ **Availability:** You're busy in the next 2 hours."
        
        else:
            # Default to today's events
            result = get_todays_events()
            events = result.get('formatted_output', 'No events found for today')
            return f"📅 **Today's Schedule:**\n\n{events}"
    
    except Exception as e:
        return f"❌ **Calendar Error:** {str(e)}"

def process_memory_query(user_input: str) -> str:
    """Process memory-related queries with strict pattern matching and similarity threshold"""
    user_input_lower = user_input.lower().strip()
    
    if not st.session_state.memory_available:
        return "❌ Memory system is not available."
    
    memory_manager = st.session_state.memory_manager
    user_id = st.session_state.user_id
    
    try:
        # Strict memory storage patterns
        if (user_input_lower.startswith('remember that ') or 
            user_input_lower.startswith('remember i ') or 
            user_input_lower.startswith('remember to ')):
            
            memory_content = user_input
            if user_input_lower.startswith('remember that '):
                memory_content = user_input.replace('remember that', '').strip()
            elif user_input_lower.startswith('remember i '):
                memory_content = user_input.replace('remember i', '').strip()
            elif user_input_lower.startswith('remember to '):
                memory_content = user_input.replace('remember to', '').strip()
            
            if memory_content and len(memory_content) > 5:
                result = memory_manager.add_memory(user_id, memory_content, "user_preference")
                if result['success']:
                    return f"💾 **Memory Stored:** \"{memory_content}\""
                else:
                    return f"❌ **Memory Error:** {result.get('error', 'Unknown error')}"
            else:
                return "❌ Please provide a valid memory to store."
        
        # Update memory pattern
        elif user_input_lower.startswith('update memory '):
            parts = user_input.split(' ', 3)
            if len(parts) >= 4:
                memory_id = parts[2]
                new_content = parts[3]
                result = memory_manager.update_memory(memory_id, new_content)
                if result['success']:
                    return f"✏️ **Memory Updated:** {memory_id}: {new_content}"
                else:
                    return f"❌ **Update Error:** {result.get('error', 'Unknown error')}"
            else:
                return "❌ **Usage:** update memory <id> <new content>"
        
        # Delete memory pattern
        elif user_input_lower.startswith('delete memory '):
            parts = user_input.split(' ', 2)
            if len(parts) >= 3:
                memory_id = parts[2]
                result = memory_manager.delete_memory(memory_id)
                if result['success']:
                    return f"🗑️ **Memory Deleted:** {memory_id}"
                else:
                    return f"❌ **Delete Error:** {result.get('error', 'Unknown error')}"
            else:
                return "❌ **Usage:** delete memory <id>"
        
        # Strict memory recall patterns
        elif (user_input_lower.startswith('recall ') or 
              user_input_lower.startswith('remember about ') or 
              user_input_lower == 'what do you remember' or 
              user_input_lower == 'my memories'):
            
            if user_input_lower == 'what do you remember' or user_input_lower == 'my memories':
                memories = memory_manager.get_memories(user_id, limit=10)['results']
                query = None
            else:
                query = user_input_lower.replace('recall', '').replace('remember about', '').strip()
                if query and len(query) > 1:
                    # Use strict similarity threshold of 0.5
                    memories = memory_manager.search_memories(user_id, query, limit=10, threshold=0.5)
                else:
                    memories = memory_manager.get_memories(user_id, limit=10)['results']
                    query = None
            
            if memories and len(memories) > 0:
                if query:
                    response = f"🔍 **Memories about '{query}':**\n\n"
                else:
                    response = "💭 **Your Memories:**\n\n"
                
                for memory in memories:
                    memory_id = memory.get('id', 'unknown')
                    memory_content = memory.get('memory', 'No content')
                    categories = memory.get('categories', [])
                    category_str = f" *[{', '.join(categories)}]*" if categories else ""
                    response += f"`{memory_id}`: {memory_content}{category_str}\n"
                
                return response
            else:
                if query:
                    return f"❌ No memories found about '{query}' with sufficient similarity (threshold: 0.5)."
                else:
                    return "❌ No memories stored yet. Use 'remember that...' to store memories."
        
        # Strict memory search patterns
        elif (user_input_lower.startswith('search memory ') or 
              user_input_lower.startswith('find in memory ')):
            
            query = user_input_lower.replace('search memory', '').replace('find in memory', '').strip()
            if query and len(query) > 1:
                # Use strict similarity threshold of 0.5
                memories = memory_manager.search_memories(user_id, query, limit=5, threshold=0.5)
                if memories and len(memories) > 0:
                    response = f"🔍 **Memory Search Results for '{query}':**\n\n"
                    for memory in memories:
                        memory_id = memory.get('id', 'unknown')
                        memory_content = memory.get('memory', 'No content')
                        response += f"`{memory_id}`: {memory_content}\n"
                    return response
                else:
                    return f"❌ No memories found for '{query}' with sufficient similarity (threshold: 0.5)."
            else:
                return "❌ Please specify what you want to search for in your memories."
        
        # Strict memory clearing patterns
        elif (user_input_lower == 'clear memories' or 
              user_input_lower == 'delete memories' or 
              user_input_lower == 'reset memories'):
            
            result = memory_manager.clear_user_memories(user_id)
            if result['success']:
                return "🗑️ **All memories have been cleared.**"
            else:
                return f"❌ **Memory Error:** {result.get('error', 'Unknown error')}"
        
        # Strict preference patterns
        elif (user_input_lower.startswith('i prefer ') or 
              user_input_lower.startswith('i like ') or 
              user_input_lower.startswith('set preference ')):
            
            preference_text = user_input
            result = memory_manager.add_memory(user_id, preference_text, "preference")
            if result['success']:
                return f"💾 **Preference Stored:** {preference_text}"
            else:
                return f"❌ **Memory Error:** {result.get('error', 'Unknown error')}"
        
        else:
            return """❌ **Unknown Memory Command.** Available commands:
- `remember that...` - Store a memory
- `recall [topic]` - Recall memories about topic  
- `search memory [query]` - Search memories
- `update memory <id> <new content>` - Update specific memory
- `delete memory <id>` - Delete specific memory
- `clear memories` - Delete all memories
- `my memories` - Show all memories
- `i prefer...` - Store preference
"""
    
    except Exception as e:
        return f"❌ **Memory System Error:** {str(e)}"

def process_user_input(user_input: str) -> str:
    """Process user input with strict command matching"""
    user_input_lower = user_input.lower().strip()
    
    # Strict command patterns for memory operations
    memory_patterns = [
        'remember that', 'remember i', 'remember to', 
        'recall', 'remember about', 'what do you remember', 'my memories',
        'search memory', 'find in memory', 'update memory', 'delete memory',
        'clear memories', 'delete memories', 'reset memories',
        'i prefer', 'i like', 'set preference'
    ]
    
    # Strict command patterns for calendar operations  
    calendar_patterns = [
        'today', "today's", 'todays', 'week', 'weekly', 'this week',
        'upcoming', 'next events', 'future events',
        'search', 'find', 'available', 'free', 'busy', 'schedule',
        'meeting', 'event', 'appointment', 'calendar'
    ]
    
    # Check for memory commands first (more specific)
    if any(user_input_lower.startswith(pattern) or pattern in user_input_lower for pattern in memory_patterns):
        return process_memory_query(user_input)
    
    # Check for calendar commands
    elif any(pattern in user_input_lower for pattern in calendar_patterns):
        if not st.session_state.calendar_authenticated:
            return "❌ **Calendar not authenticated.** Please authenticate first using the button in the sidebar."
        return process_calendar_query(user_input)
    
    # Help command
    elif user_input_lower in ['help', 'commands', 'what can you do']:
        return """🤖 **Available Commands:**

📅 **Calendar Commands:**
- "today" / "today's schedule" - Show today's events
- "week" / "weekly schedule" - Show this week's events  
- "upcoming events" - Show upcoming events
- "search [query]" - Search events
- "available" / "free time" - Check availability
- "next free slot" - Find next available time

💭 **Memory Commands:**
- "remember that..." - Store a memory
- "remember i..." - Store personal memory
- "remember to..." - Store reminder
- "recall [topic]" - Recall memories about topic
- "my memories" - Show all memories
- "search memory [query]" - Search memories
- "update memory <id> <new content>" - Update specific memory
- "delete memory <id>" - Delete specific memory
- "clear memories" - Delete all memories
- "i prefer..." - Store preference

💡 **Examples:**
- "remember that I prefer morning workouts"
- "recall meeting preferences" 
- "search memory project deadline"
- "update memory abc123 I prefer afternoon workouts"
- "delete memory def456"
- "today's schedule"
- "am I free tomorrow?"
"""
    
    # Greeting
    elif user_input_lower in ['hello', 'hi', 'hey', 'greetings']:
        return "👋 Hello! I'm your personal assistant. Type 'help' to see available commands."
    
    else:
        return "❌ **Command not recognized.** Type 'help' to see available commands for calendar and memory management."

def main():
    st.set_page_config(
        page_title="Personal Assistant",
        page_icon="🤖",
        layout="wide"
    )
    
    initialize_session_state()
    
    # Sidebar
    st.sidebar.title("🤖 Personal Assistant")
    st.sidebar.markdown("---")
    
    # User Settings
    st.sidebar.subheader("👤 User Settings")
    user_id = st.sidebar.text_input("User ID", value=st.session_state.user_id)
    if user_id != st.session_state.user_id:
        st.session_state.user_id = user_id
        st.sidebar.success(f"User ID updated to: {user_id}")
    
    # Calendar Authentication
    st.sidebar.subheader("📅 Calendar Settings")
    if st.session_state.calendar_authenticated:
        st.sidebar.success("✅ Calendar Authenticated")
        if st.sidebar.button("Re-authenticate Calendar"):
            st.session_state.calendar_authenticated = False
    else:
        st.sidebar.warning("🔒 Calendar Not Authenticated")
        if st.sidebar.button("Authenticate Calendar"):
            if authenticate_calendar_service():
                st.sidebar.success("Calendar authenticated successfully!")
                st.rerun()
    
    # Memory System Status
    st.sidebar.subheader("💭 Memory System")
    if st.session_state.memory_available:
        st.sidebar.success("✅ mem0 Connected")
        
        # Memory quick actions
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("View Memories"):
                memories = st.session_state.memory_manager.get_memories(st.session_state.user_id, limit=10)['results']
                if memories:
                    memory_text = "💭 **Your Memories:**\n\n"
                    for memory in memories:
                        memory_id = memory.get('id', 'unknown')
                        memory_content = memory.get('memory', 'No content')
                        categories = memory.get('categories', [])
                        category_str = f" *[{', '.join(categories)}]*" if categories else ""
                        memory_text += f"`{memory_id}`: {memory_content}{category_str}\n"
                    
                    st.session_state.chat_history.append({
                        'user': 'Assistant',
                        'message': memory_text,
                        'timestamp': datetime.now().isoformat()
                    })
                    st.rerun()
                else:
                    st.session_state.chat_history.append({
                        'user': 'Assistant',
                        'message': "❌ No memories stored yet.",
                        'timestamp': datetime.now().isoformat()
                    })
                    st.rerun()
        
        with col2:
            if st.button("Clear Memories"):
                result = st.session_state.memory_manager.clear_user_memories(st.session_state.user_id)
                if result['success']:
                    st.sidebar.success("Memories cleared!")
                    st.session_state.chat_history.append({
                        'user': 'Assistant',
                        'message': "🗑️ All memories have been cleared.",
                        'timestamp': datetime.now().isoformat()
                    })
                    st.rerun()
                else:
                    st.sidebar.error("Failed to clear memories")
    else:
        st.sidebar.error("❌ mem0 Not Available")
        if hasattr(st.session_state, 'memory_error'):
            st.sidebar.error(f"Error: {st.session_state.memory_error}")
    
    # Quick Actions
    st.sidebar.subheader("⚡ Quick Actions")
    
    if st.sidebar.button("Today's Schedule"):
        user_input = "today"
        st.session_state.chat_history.append({
            'user': 'User',
            'message': user_input,
            'timestamp': datetime.now().isoformat()
        })
        response = process_user_input(user_input)
        st.session_state.chat_history.append({
            'user': 'Assistant',
            'message': response,
            'timestamp': datetime.now().isoformat()
        })
        st.rerun()
    
    if st.sidebar.button("Weekly Overview"):
        user_input = "week"
        st.session_state.chat_history.append({
            'user': 'User',
            'message': user_input,
            'timestamp': datetime.now().isoformat()
        })
        response = process_user_input(user_input)
        st.session_state.chat_history.append({
            'user': 'Assistant',
            'message': response,
            'timestamp': datetime.now().isoformat()
        })
        st.rerun()
    
    if st.sidebar.button("Show Help"):
        user_input = "help"
        st.session_state.chat_history.append({
            'user': 'User',
            'message': user_input,
            'timestamp': datetime.now().isoformat()
        })
        response = process_user_input(user_input)
        st.session_state.chat_history.append({
            'user': 'Assistant',
            'message': response,
            'timestamp': datetime.now().isoformat()
        })
        st.rerun()
    
    if st.sidebar.button("Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()
    
    # Main chat interface
    st.title("🤖 Personal Assistant")
    st.markdown("""
    **Command-based assistant** for calendar and memory management.
    
    💡 **Type 'help' to see all available commands**
    """)
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for chat in st.session_state.chat_history[-20:]:
            if chat['user'] == 'User':
                st.markdown(f"""
                <div style='background-color: #e1f5fe; padding: 10px; border-radius: 10px; margin: 5px 0;'>
                    <strong>You:</strong> {chat['message']}
                </div>
                """, unsafe_allow_html=True)
            else:
                message = chat['message'].replace('\n', '<br>')
                st.markdown(f"""
                <div style='background-color: #f3e5f5; padding: 10px; border-radius: 10px; margin: 5px 0;'>
                    <strong>Assistant:</strong><br>{message}
                </div>
                """, unsafe_allow_html=True)
    
    # Chat input
    st.markdown("---")
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input(
            "Enter command...",
            key="user_input",
            placeholder="Type a command or 'help' for options..."
        )
    
    with col2:
        send_button = st.button("Send", use_container_width=True)
    
    # Process user input
    if send_button and user_input:
        st.session_state.chat_history.append({
            'user': 'User',
            'message': user_input,
            'timestamp': datetime.now().isoformat()
        })
        
        response = process_user_input(user_input)
        
        st.session_state.chat_history.append({
            'user': 'Assistant',
            'message': response,
            'timestamp': datetime.now().isoformat()
        })
        
        st.rerun()

if __name__ == "__main__":
    main()