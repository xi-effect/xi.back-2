def user_room(user_id: int) -> str:
    """
    Room for coordination of different Clients that a User has.
    Every Client is connected to one of these rooms automatically on connection.
    Clients can not leave this room
    """
    return f"user-{user_id}"


def community_room(community_id: int) -> str:
    """
    Room for updates about the current community.
    Only one such room should be active per-sid in normal operation.
    Any participant of a given community can enter this room.
    Clients can leave the room via a special event (`close-community`)
    """
    return f"community-{community_id}"


def participant_room(community_id: int, user_id: int) -> str:
    """
    Room for updates about the participation in the current community.
    Only one such room should be active per-sid in normal operation.
    Any participant of a given community can enter this room, using special events
    (`retrieve-community`, `retrieve-any-community`, `create-community`, `join-community`).
    Clients can leave the room via a special event (`close-community`)
    """
    return f"participant-{community_id}-{user_id}"


def participants_list_room(community_id: int) -> str:
    """
    Room for updates about the list of participants for a community.
    Any participant of a given community can enter this room (`list-participants`).
    Clients can leave the room via a special event (`close-participants`)
    """
    return f"community-{community_id}-participants"
