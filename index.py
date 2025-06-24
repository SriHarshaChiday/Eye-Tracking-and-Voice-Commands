import threading
import time
import cv2
import mediapipe as mp
import pyautogui as pag
import speech_recognition as sr

stop_event = threading.Event()
exit_event = threading.Event()

def stop_cursor():
    stop_event.set()

def resume_cursor():
    stop_event.clear()

def execute_command(command):
    if "stop" in command:
        stop_cursor()
        print("Stopping cursor movement.")
        return

    if "resume" in command:
        resume_cursor()
        print("Resuming cursor movement.")
        return

    if "double click" in command:
        pag.doubleClick()
        print("Double clicked.")
        return

    if "right click" in command:
        pag.click(button="right")
        print("Right click.")
        return

    if "click" in command:
        pag.click()
        print("Clicked.")
        return

    if "enter" in command:
        pag.press("enter")
        print("Pressed enter.")
        return

    if "exit" in command:
        print("Exiting program.")
        exit_event.set()
        return

def voice_control():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.3)
        print("Voice control active. Say a command (e.g., 'click', 'stop').")

        while not exit_event.is_set():
            try:
                audio = recognizer.listen(source)
                command = recognizer.recognize_google(audio).lower()
                print(f"You said: {command}")
                execute_command(command)
            except sr.UnknownValueError:
                print("I couldn't understand what you said. Please try again.")
            except sr.RequestError as e:
                print(f"Could not request results; {e}")

def gaze_control():
    cam = cv2.VideoCapture(0)
    face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
    screen_w, screen_h = pag.size()
    print("Screen dimensions: ", screen_w, "x", screen_h)

    while not exit_event.is_set():
        if stop_event.is_set():
            time.sleep(0.1)
            continue

        ret, frame = cam.read()
        if not ret:
            print("Failed to capture frame.")
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)
        landmarks_points = results.multi_face_landmarks

        if landmarks_points:
            landmarks = landmarks_points[0].landmark
            for id, point in enumerate(landmarks[474:478]):
                x = int(point.x * frame.shape[1])
                y = int(point.y * frame.shape[0])
                cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

                if id == 1:
                    screen_x = screen_w / frame.shape[1] * x
                    screen_y = screen_h / frame.shape[0] * y
                    pag.moveTo(screen_x, screen_y)

            left_eye = [landmarks[145], landmarks[159]]
            right_eye = [landmarks[374], landmarks[386]]
            for landmark in right_eye + left_eye:
                x = int(landmark.x * frame.shape[1])
                y = int(landmark.y * frame.shape[0])
                cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

        cv2.imshow("Camera Control", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cam.release()
    face_mesh.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    threading.Thread(target=voice_control, daemon=True).start()
    gaze_control()
    exit_event.set()
