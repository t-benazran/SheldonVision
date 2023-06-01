from typing import List, Tuple


class NotificationMessage:
    def __init__(self, title: str, body: str, notification_type: dict):
        self.title = title
        self.body = body
        self.notification_type = notification_type


class Notification:
    __info = {'color': 'blue', 'icon': 'ic:outline-announcement', 'style': {'background-color': '#DBE9FA'}, 'autoClose': 5000}
    __warning = {'color': 'orange', 'icon': 'ic:round-warning-amber', 'style': {'background-color': '#FED8B1'}, 'autoClose': 7000}
    __error = {'color': 'red', 'icon': 'ic:round-error', 'style': {'background-color': 'pink'}, 'autoClose': False}

    def __init__(self):
        self.__notifications: List[NotificationMessage] = []
        self.__notifications_counter: int = 0

    def notify_info(self, title: str, body: str) -> None:
        self.__notifications.append(NotificationMessage(title=title, body=body, notification_type=self.__info))

    def notify_warning(self, title: str, body: str) -> None:
        self.__notifications.append(NotificationMessage(title=title, body=body, notification_type=self.__warning))

    def notify_error(self, title: str, body: str) -> None:
        self.__notifications.append(NotificationMessage(title=title, body=body, notification_type=self.__error))

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
        self.__notifications_counter += 1
        return notification, self.__notifications_counter
