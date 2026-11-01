import cv2
import numpy as np
from PIL import Image
import os

def generateMotionVideo(frames, mode="Moving", threshold=25):
    if len(frames) < 2:
        return []
    pil_masks = []
    if mode == "Moving":
        for i in range(len(frames) - 1):
            mask_array = frameDifference(frames[i], frames[i+1], threshold)
            pil_img = Image.fromarray(mask_array, mode='L').convert('RGB')
            pil_masks.append(pil_img)
    elif mode == "Trail":
        accumulated_diff = np.zeros_like(frames[0], dtype=np.uint8) 
        for i in range(len(frames) - 1):
            mask_array = frameDifference(frames[i], frames[i+1], threshold)
            accumulated_diff = np.maximum(accumulated_diff, mask_array)
            pil_img = Image.fromarray(accumulated_diff.copy(), mode='L').convert('RGB')
            pil_masks.append(pil_img)

    return pil_masks

def loadVideoToMatrices(videoPath, targetWidth = 640, targetHeight = 360):
    cap = cv2.VideoCapture(videoPath)
    if not cap.isOpened():
        print(f"Failed to open video file: {videoPath}")
        return [], 0
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = []
    frameCount = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, (targetWidth, targetHeight))
        greyMatrix = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frames.append(greyMatrix)
        frameCount += 1
    cap.release()
    return frames, fps


#doesnt work as intended
def frameDifference(frame1, frame2, margin=25):
    diff = np.abs(frame1.astype(np.int16) - frame2.astype(np.int16))
    baseline = np.mean(diff)
    dynamic_threshold = baseline + margin
    motionMask = np.where(diff > dynamic_threshold, 255, 0).astype(np.uint8)
    return motionMask


#old frame diff code
# def frameDifference(frame1,frame2,threshold = 25):
#     diff = np.abs(frame1.astype(np.int16) - frame2.astype(np.int16))
#     motionMask = np.where(diff > threshold, 255, 0).astype(np.uint8)
#     return motionMask

