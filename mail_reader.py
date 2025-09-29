import imaplib
import email
from email.header import decode_header
from os import getenv
import re
import time

# Thông tin đăng nhập Yandex Mail
usernameYandex = getenv("usernameYandex") # Email/SĐT tài khoản Yandex
apppasswordYandex = getenv("apppasswordYandex") # Mật khẩu tài khoản Entrade

# Kết nối tới máy chủ IMAP của Yandex
def authenticate_yandex():
    imap_server = "imap.yandex.com"
    imap_port = 993
    # Kết nối với máy chủ IMAP của Yandex
    mail = imaplib.IMAP4_SSL(imap_server, imap_port)

    try:
        # Đăng nhập bằng tên người dùng và mật khẩu ứng dụng
        mail.login(usernameYandex, apppasswordYandex)
        return mail
    except imaplib.IMAP4.error as e:
        print("Đăng nhập imap thất bại:", e)
        return None

def get_otp_from_yandex(mail):
    try:
        
        time.sleep(5)   # tạm dừng 5s đợi thư OTP về mail

        # Chọn hộp thư cần kiểm tra (INBOX)
        mail.select('Inbox')
        
        # Tìm email chưa đọc từ địa chỉ cụ thể (ví dụ từ noreply@otp.com) và có từ khóa trong tiêu đề
        # status, messages = mail.search(None, '(UNSEEN FROM "noreply@mail.dnse.com.vn" SUBJECT "Email OTP")')
        status, messages = mail.search(None, '(UNSEEN FROM "noreply@mail.dnse.com.vn" SUBJECT "Email OTP")')
        # Nếu tìm thấy email, xử lý
        if status == "OK":
            msg_ids = messages[0].split()
            latest_msg_id = msg_ids[-1]
            status, msg_data = mail.fetch(latest_msg_id, "(RFC822)")
            
            if status == "OK":
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                            
                        # Trích xuất nội dung email
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))
                                if "attachment" not in content_disposition:
                                    # Trích xuất text/plain
                                    if content_type == "text/plain":
                                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                        # Tìm OTP trong nội dung email
                                        otp = extract_otp_from_body(body)
                                        if otp:
                                            print(f"OTP: {otp}")
                                            return otp
                        else:
                            # Nếu email không phải multipart
                            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                            otp = extract_otp_from_body(body)
                            if otp:
                                print(f"OTP: {otp}")
                                return otp
            mail.store(latest_msg_id, '+FLAGS', '\\Seen')
        else:
            print("Không tìm thấy email OTP.")
        return None
    except:
        return None

# Hàm để trích xuất OTP từ nội dung email
def extract_otp_from_body(body):
    # Giả sử OTP là một chuỗi số 6 chữ số
    match = re.search(r'\b\d{6}\b', body)
    if match:
        return match.group(0)
    return None

def getOTP():
    mail = authenticate_yandex()
    if mail:
        otp = get_otp_from_yandex(mail)
        # if otp:
        #     print(f"OTP là: {otp}")
        mail.logout()
    return otp


# if __name__ == "__main__":
#     getOTP()
