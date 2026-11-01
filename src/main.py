from cmu_graphics import *
import os
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
from videoProcessor import loadVideoToMatrices, generateMotionVideo
from PIL import Image
import json
import random
import urllib.request

#All videos are taken off https://www.pexels.com or from my own personal camera roll.

def loadQuestionsData():
    json_path = os.path.join(script_dir, "questions.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading questions.json: {e}")
    return [
        {
            "question": 1,
            "videoPath": os.path.join("assets", "videos", "video1.mp4"),
            "options": ["Palm Tree", "Waves", "Wind", "Windmill"],
            "correctAnswer": "Palm Tree"
        },
        {
            "question": 2,
            "videoPath": os.path.join("assets", "videos", "carvid.mp4"),
            "options": ["Cars", "Truck", "Plane", "Bird"],
            "correctAnswer": "Cars"
        }
    ]

def saveQuestionsData(questions):
    json_path = os.path.join(script_dir, "questions.json")
    try:
        with open(json_path, "w") as f:
            json.dump(questions, f, indent=4)
    except Exception as e:
        print(f"Error saving to questions.json: {e}")

def onAppStart(app):
    app.width = 800
    app.height = 600
    app.stepsPerSecond = 24 
    app.background = "black"
    app.statusMsg = "No video loaded"
    app.userAnswer = ""
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    video_path = os.path.join(project_root, 'assets', 'videos', 'video1.mp4')
    
    print("Pre-processing video frames into motion silhouettes...")
    raw_frames, app.fps = loadVideoToMatrices(video_path, targetWidth=640, targetHeight=360)
    
    app.pil_Frames = []
    app.currentFrameIndex = 0

    app.screen = "menu"
    app.mode = 'Multiple Choice'
    app.difficulty = 'Moving'
    app.timer = 30
    app.score = 0
    app.uploadPathInput = ""      
    app.uploadAnswerInput = ""    
    app.activeInputField = "path" 
    app.questions = loadQuestionsData()
    app.currentQuestionIndex = 0
    app.questionHistory = []
    app.currentStreak = 0 
    app.bestStreak = 0

def drawButton(x, y, w, h, text, fill='white', border='grey', textColor='black'):
    drawRect(x, y, w, h, fill=fill, border=border, borderWidth=2)
    drawLabel(text, x + w / 2, y + h / 2, size=18, fill=textColor, bold=True)

def isClicked(mouseX, mouseY, x, y, w, h):
    return (x <= mouseX <= x + w) and (y <= mouseY <= y + h)

def getCurrentQuestion(app):
    return app.questions[app.currentQuestionIndex]

def getQuestionText(app):
    quest = getCurrentQuestion(app)
    return f"Question {app.currentQuestionIndex + 1} of {len(app.questions)}: What is moving?"

def onStep(app):
    if app.screen == "game":
        if app.cmu_Frames:
            app.currentFrameIndex = (app.currentFrameIndex + 1) % len(app.cmu_Frames)
        app.timer -= 1 / app.stepsPerSecond
        if app.timer <= 0:
            processAnswer(app, selectedOption = None)

def redrawAll(app):
    if app.screen == 'menu':
        drawMainMenu(app)
    elif app.screen == 'setup':
        drawSetupScreen(app)
    elif app.screen == 'upload':
        drawUploadScreen(app)
    elif app.screen == 'game':
        drawGameScreen(app)
    elif app.screen == 'summary':
        drawSummaryScreen(app)

def drawMainMenu(app):
    drawLabel("Object Guess", app.width / 2, 140, size=36, fill='white', bold=True)
    drawButton(app.width / 2 - 120, 220, 240, 45, 'Start Game')
    drawButton(app.width / 2 - 120, 280, 240, 45, 'Upload Video')
    drawButton(app.width / 2 - 120, 340, 240, 45, 'Settings')
    drawLabel(f"Loaded Questions: {len(app.questions)}", app.width / 2, 420, size=16, fill='cyan')
    drawLabel(app.statusMsg, app.width / 2, 460, size=14, fill='grey')

def drawSetupScreen(app):
    drawLabel("Game Setup", app.width / 2, 80, size = 36, fill = 'white', bold = True)
    drawLabel(f"Mode: [{app.mode}]", app.width / 2, 170, size = 20, fill = 'white')
    diffText = "Moving (full video)" if app.difficulty == 'Moving' else "Trail (object creates a trail)"
    drawLabel(f"Difficulty: [{diffText}]", app.width / 2, 240, size = 20, fill = 'white')
    drawButton(app.width / 2 - 120, 400, 240, 45, 'Play Game')
    drawButton(app.width / 2 - 120, 460, 240, 45, 'Back to Menu')

def drawUploadScreen(app):
    drawLabel("Upload New Video Question", app.width / 2, 60, size=30, fill='white', bold=True)
    
    p_color = 'yellow' if app.activeInputField == "path" else 'white'
    drawLabel("1. Video File Path (e.g., assets/videos/myvid.mp4):", app.width / 2, 130, size=16, fill='white')
    drawRect(150, 155, 500, 40, fill='white', border=p_color, borderWidth=3)
    drawLabel(app.uploadPathInput[-40:], 400, 175, size=16, fill='black')

    a_color = 'yellow' if app.activeInputField == "answer" else 'white'
    drawLabel("2. Correct Answer (e.g., Cat):", app.width / 2, 220, size=16, fill='white')
    drawRect(150, 245, 500, 40, fill='white', border=a_color, borderWidth=3)
    drawLabel(app.uploadAnswerInput, 400, 265, size=16, fill='black')

    drawLabel("* Distractors will be automatically generated via Datamuse API!", app.width / 2, 310, size=14, fill='lightGreen')

    drawButton(app.width / 2 - 120, 360, 240, 45, 'Save Question', fill='lightGreen')
    drawButton(app.width / 2 - 120, 430, 240, 45, 'Back to Menu')
    
    if app.statusMsg:
        drawLabel(app.statusMsg, app.width / 2, 510, size=16, fill='orange')

def drawGameScreen(app):
    quest = getCurrentQuestion(app)
    drawLabel(getQuestionText(app), app.width / 2, 40, size = 22, fill = 'white', bold = True)
    drawLabel(f"Score: {app.score}", app.width - 120, 80, size = 18, fill = 'white')
    drawLabel(f"Time Left: {int(app.timer)}", 120, 80, size = 18, fill = 'white')
    drawRect(50,110,420,380,fill = None, border = 'white', borderWidth = 2)
    if app.cmu_Frames:
        cmu_img = app.cmu_Frames[app.currentFrameIndex]
        drawImage(cmu_img, 60, 120, width=400, height=360)
    else: 
        drawLabel("loading Video...", 260, 300, size = 16, fill = 'grey')
    if app.mode == 'Multiple Choice':
        for i, option in enumerate(quest['options']):
            qy = 140 + (i * 70)
            drawRect(500, qy, 240, 50, fill='white', border = 'grey', borderWidth =2)
            drawLabel(f"{option}", 620, qy + 25, size=18, fill='black', bold=True)
    elif app.mode == 'Free Response':
        drawLabel("Type your answer below:", 620, 150, size=18, fill='white', bold=True)
        drawRect(500, 180, 240, 50, fill='white', border='yellow', borderWidth=2)
        cursor = "|" if (app.currentFrameIndex % 12 < 6) else ""   
        drawLabel(f"{app.userAnswer}{cursor}", 620, 205, size=18, fill='black', bold=True)
        drawButton(500, 250, 240, 45, 'Submit (Enter)')

def drawSummaryScreen(app):
    drawLabel("Final Score Summary", app.width / 2, 80, size = 36, fill = 'white', bold = True)
    for i, (questionNum, isCorrect) in enumerate(app.questionHistory):
        status = "correct!" if isCorrect else"Incorrect :("
        color = 'lightGreen' if isCorrect else 'red'
        drawLabel(f"Question {questionNum}: {status}", app.width / 2, 160 + (i * 40), size = 20, fill = color)
    drawLabel(f"Final Score: {app.score} / {len(app.questions)}", app.width / 2, 370, size = 24, fill = 'white', bold = True)
    streakText = f"Best Answer Streak: {app.bestStreak}"
    drawLabel(streakText, app.width / 2, 410, size=20, fill='white', bold=True)
    drawButton(app.width / 2 - 120, 460, 260, 45, 'Back to Menu')

def onKeyPress(app, key):
    if app.screen == 'upload':
        target = "uploadPathInput" if app.activeInputField == "path" else "uploadAnswerInput"
        curr_val = getattr(app, target)
        if key == 'backspace':
            setattr(app, target, curr_val[:-1])
        elif key == 'space':
            setattr(app, target, curr_val + " ")
        elif len(key) == 1:
            setattr(app, target, curr_val + key)
    elif app.screen == 'game' and app.mode == 'Free Response':
        if key == 'enter':
            processAnswer(app, app.userAnswer)
        elif key == 'backspace':
            app.userAnswer = app.userAnswer[:-1]
        elif key == 'space':
            app.userAnswer += ' '
        elif len(key) == 1:
            app.userAnswer += key

def onMousePress(app, mouseX, mouseY):
    if app.screen == 'menu':
        if isClicked(mouseX, mouseY, app.width / 2 - 120, 220, 240, 45):
            startGame(app)
        elif isClicked(mouseX, mouseY, app.width / 2 - 120, 280, 240, 45):
            app.screen = 'upload'
            app.statusMsg = ""
        elif isClicked(mouseX, mouseY, app.width / 2 - 120, 340, 240, 45):
            app.screen = 'setup'
    elif app.screen == 'upload':
        if isClicked(mouseX, mouseY, 150, 155, 500, 40):
            app.activeInputField = "path"
        elif isClicked(mouseX, mouseY, 150, 245, 500, 40):
            app.activeInputField = "answer"
        elif isClicked(mouseX, mouseY, app.width / 2 - 120, 360, 240, 45):
            saveUploadedQuestion(app)
        elif isClicked(mouseX, mouseY, app.width / 2 - 120, 430, 240, 45):
            app.screen = 'menu'
    elif app.screen == 'setup':
        if isClicked(mouseX, mouseY, app.width / 2 - 150, 150, 300, 40):
            app.mode = 'Free Response' if app.mode == 'Multiple Choice' else 'Multiple Choice'
        elif isClicked(mouseX, mouseY, app.width / 2 - 180, 220, 360, 40):
            app.difficulty = 'Moving' if app.difficulty == 'Trail' else 'Trail'
        elif isClicked(mouseX, mouseY, app.width / 2 - 120, 400, 240, 45):
            startGame(app)
        elif isClicked(mouseX, mouseY, app.width / 2 - 120, 460, 240, 45):
            app.screen = 'menu'
    elif app.screen == 'game':
        if app.mode == 'Multiple Choice':
            quest = getCurrentQuestion(app)
            for i, option in enumerate(quest['options']):
                y_pos = 140 + (i * 70)
                if isClicked(mouseX, mouseY, 500, y_pos, 240, 50):
                    processAnswer(app, option)
        elif app.mode == 'Free Response':
            if isClicked(mouseX, mouseY, 500, 250, 240, 45):
                processAnswer(app, app.userAnswer)
    elif app.screen == 'summary':
        if isClicked(mouseX, mouseY, app.width / 2 - 120, 460, 240, 45):
            app.screen = 'menu'

def startGame(app):
    app.currentQuestionIndex = 0
    app.score = 0
    app.questionHistory = []
    loadCurrentVideo(app)
    app.screen = 'game'
    app.currentStreak = 0 
    app.bestStreak = 0

def loadCurrentVideo(app):
    quest = getCurrentQuestion(app)
    app.timer = 30
    app.userAnswer = ""
    if 'options' in quest and isinstance(quest['options'], list):
        random.shuffle(quest['options'])
    full_video_path = os.path.abspath(os.path.join(script_dir, quest['videoPath']))
    if not os.path.exists(full_video_path):
        parent_dir = os.path.dirname(script_dir)
        full_video_path = os.path.abspath(os.path.join(parent_dir, quest['videoPath']))
    app.statusMsg = f"Loading {quest['videoPath']}..."
    raw_frames, fps = loadVideoToMatrices(full_video_path, targetWidth=400, targetHeight=360)
    pil_frames = generateMotionVideo(raw_frames, mode=app.difficulty, threshold=25)
    app.cmu_Frames = [CMUImage(img) for img in pil_frames]
    app.currentFrameIndex = 0

# Lines 276-339 citation "https://docs.python.org/3/howto/urllib2.html" "https://docs.python.org/3/library/urllib.request.html"
#For HTTP GET requests to fetch RESTful API JSON payloads
# lines 310-339 "https://www.datamuse.com/api/" 
# #Used for context-aware distractor generation via means-like semantic query (`ml`).

def saveUploadedQuestion(app):
    v_path = app.uploadPathInput.strip()
    ans = app.uploadAnswerInput.strip()

    if not v_path or not ans:
        app.statusMsg = "Please enter both a video path and an answer!"
        return

    full_path = os.path.abspath(os.path.join(script_dir, v_path))
    if not os.path.exists(full_path):
        project_root = os.path.dirname(script_dir)
        full_path = os.path.abspath(os.path.join(project_root, v_path))
    if not os.path.exists(full_path) and os.path.exists(v_path):
        full_path = os.path.abspath(v_path)

    if not os.path.exists(full_path):
        app.statusMsg = "File not found! Double check path."
        return

    options = generateDistractors(ans)
    new_q = {
        "question": len(app.questions) + 1,
        "videoPath": v_path,
        "correctAnswer": ans.title(),
        "options": options
    }

    app.questions.append(new_q)
    saveQuestionsData(app.questions)
    
    app.uploadPathInput = ""
    app.uploadAnswerInput = ""
    app.statusMsg = "Question saved successfully!"

def generateDistractors(answer, numDistractors=3):
    clean_ans = answer.strip().title()
    distractors = []
    # all similar words are taken from the Datamuse API
    try:
        url = f"https://api.datamuse.com/words?ml={clean_ans}&max=15"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, timeout=3) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                for entry in data:
                    word = entry.get('word', '').strip().title()
                    if word and word.lower() != clean_ans.lower() and word not in distractors:
                        distractors.append(word)
                    if len(distractors) >= numDistractors:
                        break
    except Exception as e:
        print(f"Datamuse API error or offline: {e}")
    fallback_pool = ["Car", "Person", "Tree", "House", "Bird", "Dog", "Cat", "Bicycle", "Boat", "Plane"]
    random.shuffle(fallback_pool)
    while len(distractors) < numDistractors:
        for word in fallback_pool:
            if word.lower() != clean_ans.lower() and word not in distractors:
                distractors.append(word)
            if len(distractors) >= numDistractors:
                break
    options = [clean_ans] + distractors[:numDistractors]
    random.shuffle(options)
    return options

def processAnswer(app, selectedOption):
    quest = getCurrentQuestion(app)
    is_correct = (selectedOption == quest['correctAnswer'])
    if selectedOption is None:
        is_correct = False
    else:
        user_clean = selectedOption.strip().lower()
        correct_clean = quest['correctAnswer'].strip().lower()
        is_correct = (user_clean == correct_clean)
    if is_correct:
        app.score += 1
        app.currentStreak += 1
        if app.currentStreak > app.bestStreak:
            app.bestStreak = app.currentStreak
    else:
        app.currentStreak = 0
    app.questionHistory.append((app.currentQuestionIndex + 1, is_correct))
    if app.currentQuestionIndex + 1 < len(app.questions):
        app.currentQuestionIndex += 1
        loadCurrentVideo(app)
    else:
        app.screen = 'summary' 

def main():
    runApp(width = 800, height = 600)

if __name__ == '__main__':
    main()