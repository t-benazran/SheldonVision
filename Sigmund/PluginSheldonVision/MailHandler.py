import io
import re
import uuid
import base64
import datetime
import requests
import win32gui
import win32com.client
from PIL import Image, ImageGrab
from functools import partial
from typing import Tuple
from PluginSheldonVision.MetaDataHandler import MetaDataType
from PluginSheldonVision.Constants import SHELDON_VISION_UI_TITLE


class MailHandler:
    toplist = []
    winlist = []
    screenshot = None

    @staticmethod
    def get_screenshot() -> Image:
        def enum_cb(hwnd, results):
            MailHandler.winlist.append((hwnd, win32gui.GetWindowText(hwnd)))

        try:
            win32gui.EnumWindows(enum_cb, MailHandler.toplist)

            screen_title = [(hwnd, title) for hwnd, title in MailHandler.winlist if SHELDON_VISION_UI_TITLE in title]
            specific_window = screen_title[0]
            hwnd = specific_window[0]

            win32gui.SetForegroundWindow(hwnd)
            bbox = win32gui.GetWindowRect(hwnd)
            ImageGrab.grab = partial(ImageGrab.grab, all_screens=True)
            MailHandler.screenshot = ImageGrab.grab(bbox)
        except:
            MailHandler.screenshot = None

    @staticmethod
    def mail_address_validator(mail_address: str, invalid_field: bool) -> Tuple[bool, bool, list]:
        if not mail_address:
            return False, False, []
        regex_mail = r"^[\w\-\.]+@([\w-]+\.)+[\w-]{2,4}$"
        all_addresses = [mail.strip() for mail in mail_address.split(',')]
        for address in all_addresses:
            if not re.match(regex_mail, address):
                return False, True, []

        return not invalid_field, False, all_addresses

    @staticmethod
    def send_with_outlook(upload_to_blob_callback, video: str, primary_metadata: str = None, secondary_metadata: str = None,
                          frame_number: int = 1):
        try:
            if not MailHandler.screenshot:
                return 'Failed to take screenshot'
            buffered = io.BytesIO()
            MailHandler.screenshot.save(buffered, format="JPEG")
            content = base64.b64encode(buffered.getvalue())
            autorun_link = MailHandler.__link_autorun(upload_to_blob_callback, video, primary_metadata, secondary_metadata, frame_number)
            html_page = f'<html><body><div>{autorun_link}</div><br><br><div>Clip: {video}<br><br></div>' \
                        f'<img src="data:image/png;base64,{str(content)[2:-1]}"></body></html>'
            outlook_mail_item = 0x0
            obj = win32com.client.Dispatch("Outlook.Application")
            new_mail = obj.CreateItem(outlook_mail_item)
            new_mail.Subject = "Mail from SheldonVision"
            new_mail.BodyFormat = 2
            new_mail.HTMLBody = html_page
            if primary_metadata:
                new_mail.Attachments.Add(Source=primary_metadata)
            if secondary_metadata:
                new_mail.Attachments.Add(Source=secondary_metadata)
            new_mail.display()
            return ''
        except Exception as ex:
            return ex

    @staticmethod
    def __link_autorun(upload_to_blob_callback, video_path, metadata_primary, metadata_secondary, frame_number):
        uid = uuid.uuid4()
        dest_path = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uid}_metadata"
        params = {'video_path': video_path, 'frame_number': frame_number}
        if metadata_primary:
            primary_blob = upload_to_blob_callback(metadata_primary, dest_path + f"/{MetaDataType.PRIMARY.value}")
            params['metadata_primary'] = primary_blob
        if metadata_secondary:
            secondary_blob = upload_to_blob_callback(metadata_secondary, dest_path + f"/{MetaDataType.SECONDARY.value}")
            params['metadata_secondary'] = secondary_blob
        prepare_request = requests.models.PreparedRequest()
        prepare_request.prepare_url(url='http://127.0.0.1:8050//autorun_from_mail',
                                    params=params)
        return f'<a href={prepare_request.url}>Load on SheldonVision</a>  <b>Sheldon Vision Must be open in order to run this link</b>'
