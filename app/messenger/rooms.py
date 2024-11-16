def chat_room(chat_id: int) -> str:
    """
    Room for updates about the current chat.
    Only one such room should be active per-sid in normal operation.
    Any participant of a given community can enter this room.
    Clients can leave the room via a special event (`close-chat`)
    """
    return f"chat-{chat_id}"
