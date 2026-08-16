def user_room(user_id: int) -> str:
    """
    Room for coordination of different Clients that a User has.
    Every Client is connected to one of these rooms automatically on connection.
    Clients can not leave this room
    """
    return f"user-{user_id}"
