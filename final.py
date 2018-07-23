import praw, json, urllib.request, time, cv2, random, pyimgur
import numpy as np


eye_cascade = cv2.CascadeClassifier('haarcascade_eye.xml')
flare = cv2.imread('flare.png', -1)

with open('config.ini', 'r') as f:
    info = f.read()

info = info.split('\n')
client = info[0]
secret = info[1]
passw = info[2]
imgur_client = info[3]

reddit = praw.Reddit(client_id = client,
                     client_secret = secret,
                     password = passw,
                     user_agent = 'bot by /u/xxjuiceboxxx',
                     username = 'nani_bot')

sub = reddit.subreddit('nani_bot')

with open('posts.json', 'r') as f:
    data = f.read()
    data = json.loads(data)

def noise(img, prob): #modifies the image
    output = np.zeros(img.shape, np.uint8)
    thres = 1 - prob
    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            rdn = random.random()
            if rdn < prob:
                output[i][j] = 0
            elif rdn > thres: #adds salt-and-pepper noise
                output[i][j] = (int(img[i][j][0]+(255-img[i][j][0])/2), int(img[i][j][1]+(255-img[i][j][1])/2), int(img[i][j][2]+(255-img[i][j][2])/2), img[i][j][3])
            else:
                output[i][j] = (int(img[i][j][0]*4/5), int(img[i][j][1]*4/5), 255, img[i][j][3])
    return output

def upload(path): #uploads result image to imgur and returns its link
    im = pyimgur.Imgur(imgur_client)
    uploaded = im.upload_image(path, title = 'test')
    return uploaded.link

def mod_img(img): #eye detection and modification
    b, g, r = cv2.split(img)
    alpha = np.ones(b.shape, dtype = b.dtype)*50
    img = cv2.merge((b, g, r, alpha))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    eyes = eye_cascade.detectMultiScale(gray, 1.3, 5)
                
    img = noise(img, 0.005)
    for (x, y, w, h) in eyes:
        print('eye detected at (%s;%s)'%(x, y))
        #cv2.rectangle(img, (x,y), (x+y, y+h), (255, 0, 0), 2)
        flare_t = cv2.resize(flare, (w, h), interpolation = cv2.INTER_CUBIC)
        y1, y2 = y, y + w
        x1, x2 = x, x + h
        alpha_s = flare_t[:, :, 3]/255.0
        alpha_l = 1.0 - alpha_s
        for c in range(0, 3):
            img[y1:y2, x1:x2, c] = (alpha_s * flare_t[:, :, c] + alpha_l * img[y1: y2, x1:x2, c])

    cv2.imwrite('result.jpg', img)
    link = upload('result.jpg')
    return link

while 1:
    comments = sub.comments(limit = 25)
    for c in comments:
        if '/u/nani_bot' in c.body.lower() and c.submission.fullname not in data['completed']:
            data['completed'].append(c.submission.fullname)
            with open('posts.json', 'w') as f:
                updates = json.dumps(data)
                f.write(updates)
            try:
                urllib.request.urlretrieve(c.submission.url, 'test.jpg')
                img = cv2.imread('test.jpg')
                result = mod_img(img)
                time.sleep(2)
                c.reply(result)
            except:
                time.sleep(2)
                c.reply('err: no picture in original post')
    time.sleep(5)
