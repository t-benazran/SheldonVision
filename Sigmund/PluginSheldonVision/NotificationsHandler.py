from typing import List, Tuple
import enum


class NotificationMessage:
    def __init__(self, title: str, body: str, notification_type: dict, notification_id: int = None, is_update: bool = False):
        self.title = title
        self.body = body
        self.notification_type = notification_type
        self.notification_id = notification_id
        self.is_update = is_update


class NotificationTypes(enum.Enum):
    Info = 0
    Error = 1
    Warning = 2


class Notification:
    __info = {'color': 'blue', 'icon': 'ic:outline-announcement', 'style': {'background-color': '#DBE9FA'}, 'autoClose': 5000}
    __warning = {'color': 'orange', 'icon': 'ic:round-warning-amber', 'style': {'background-color': '#FED8B1'}, 'autoClose': 7000}
    __error = {'color': 'red', 'icon': 'ic:round-error', 'style': {'background-color': '#FFC0CB'}, 'autoClose': False}

    def __init__(self):
        self.__notifications: List[NotificationMessage] = []
        self.__notifications_counter: int = 0

    def notify_info(self, title: str, body: str) -> None:
        self.__notifications.append(NotificationMessage(title=title, body=body, notification_type=self.__info))

    def notify_warning(self, title: str, body: str) -> None:
        self.__notifications.append(NotificationMessage(title=title, body=body, notification_type=self.__warning))

    def notify_error(self, title: str, body: str) -> None:
        self.__notifications.append(NotificationMessage(title=title, body=body, notification_type=self.__error))

    def close_error(self, notification_id: int) -> None:
        self.__notifications.append(NotificationMessage(title='', body='', notification_type=self.__error, notification_id=notification_id))

    def get_notification(self) -> Tuple[NotificationMessage | None, int]:
        if not self.__notifications:
            return None, 0

        notification_id_error = [indx for indx, notify in enumerate(self.__notifications) if notify.notification_type == self.__error]
        notification_id_warning = [indx for indx, notify in enumerate(self.__notifications) if notify.notification_type == self.__warning]
        if notification_id_error:
            notification = self.__notifications.pop(notification_id_error[0])
        elif notification_id_warning:
            notification = self.__notifications.pop(notification_id_warning[0])
        else:
            notification = self.__notifications.pop(0)
        if notification.notification_id is None:
            self.__notifications_counter += 1
            return notification, self.__notifications_counter
        else:
            return notification, notification.notification_id

    def get_notification_type(self, notification: NotificationMessage | dict) -> NotificationTypes:
        returned_type = NotificationTypes.Info
        if isinstance(notification, dict):
            props = notification['props']
            notification_type = {'color': props['color'], 'icon': props['icon']['props']['icon'], 'style': props['style'],
                                 'autoClose': props['autoClose']}
        else:
            notification_type = notification.notification_type
        match notification_type:
            case self.__error:
                returned_type = NotificationTypes.Error
            case self.__info:
                returned_type = NotificationTypes.Info
            case self.__warning:
                returned_type = NotificationTypes.Warning
        return returned_type
