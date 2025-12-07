import cv2
from pyzbar import pyzbar
import time

def main():

    # Timer variables
    show_message = False
    message_start_time = 0
    message_text = ""

    # Student list
    QR_list = [f"25MCA{str(i).zfill(2)}" for i in range(1, 61)]

    Present_studs = []

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Cannot access camera")
        return
    
    print("Camera started. Show the QR code in the ID card to the webcam to Mark Attendance")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        qr_codes = pyzbar.decode(frame)
  
        if not qr_codes:
            inverted_frame = cv2.bitwise_not(frame)
            qr_codes = pyzbar.decode(inverted_frame)

        for qr in qr_codes:

            qr_data = qr.data.decode("utf-8")
            qr_id = qr_data[0:7]
            # print("QR Code Detected:", qr_id)

            (x, y, w, h) = qr.rect
            cv2.rectangle(frame, (x, y), (x+w, y+h), (200, 200, 255), 2)


            if qr_id in QR_list:

                Present_studs.append(qr_id)
                QR_list.remove(qr_id)

                # Set message for 3 seconds
                message_text = "Attendance Marked Successfully: " + qr_id
                show_message = True
                message_start_time = time.time()

                cv2.putText(frame, "Attendance Marked: " + qr_id,
                            (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, (200, 200, 255), 2)



            elif qr_id in Present_studs:

                # message_text = "Attendance Already Marked: " + qr_id
                # show_message = True
                # message_start_time = time.time()

                cv2.putText(frame, "Attendance Already Marked: ",
                            (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, (0, 255, 0), 2)


            else:
                message_text = "Unknown QR Code"
                show_message = True
                message_start_time = time.time()

                cv2.putText(frame, "Unknown QR Code",
                            (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, (0, 0, 255), 2)

        if show_message:
            cv2.putText(frame,
                        message_text,
                        (20, frame.shape[0] - 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (255, 255, 255), 3)

            if time.time() - message_start_time > 3:
                show_message = False

        # Heading
        cv2.putText(frame,"Take Haajar",
                    (20, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,(255, 180, 180), 1)

        cv2.imshow("QR Scanner", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return Present_studs
    # print("\nAttendance List:")
    # print(Present_studs)


if __name__ == "__main__":
    a=main()
    print(a)
