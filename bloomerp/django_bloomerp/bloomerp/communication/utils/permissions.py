


from bloomerp.models.communication.inbox.inbox_folder import InboxFolder
from bloomerp.models.users.user import AbstractBloomerpUser


def user_has_access_to_inbox_folder(user:AbstractBloomerpUser, inbox_folder:InboxFolder) -> bool:
    """
    Checks if a user has access to a specific inbox folder.

    Args:
        user (User): The user object.
        inbox_folder (InboxFolder): The inbox folder object.

    Returns:
        bool: True if the user has access, False otherwise.
    """
    # TODO
    return True