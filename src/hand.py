import cv2
import numpy as np
import random
import tkinter
from PIL.ImageTk import PhotoImage
from PIL.Image import fromarray
from tkinter import filedialog
from tkinter.messagebox import showerror

class Img_handle:
    def __init__(self,area_min,lenth_min,distance,drawtype=0,area_max=100000,lenth_max=100000):
        #default area_min=20000 lenth_min=1000 distance=300
        self.area_min=area_min
        self.area_max=area_max
        self.lenth_min=lenth_min
        self.lenth_max=lenth_max
        self.distance=distance
        self.allpoint = []
        self.highHSV = np.array([15, 255, 255])
        self.lowHSV = np.array([0, 50, 50])
        self.drawtype=drawtype

    def change_distance(self,distance):
        self.distance=distance

    def change_Hsv(self,lowHSV,highHSV):
        self.highHSV=highHSV
        self.lowHSV=lowHSV

    def resize_img(self,size=list,img=None):
        if np.any(img):
            self.img=img
        size = [size[1], size[0], size[2]]
        mask = np.zeros(size, dtype=np.uint8)
        h, w = self.img.shape[0:2]
        dwh = min([size[0] / h, size[1] / w])
        self.img = cv2.resize(self.img, None, fx=dwh, fy=dwh)
        if h > w:
            dxy = int((size[1] - self.img.shape[1]) / 2)
            mask[:, dxy:self.img.shape[1] + dxy, :] = self.img
        else:
            dxy = int((size[0] - self.img.shape[0]) / 2)
            mask[dxy:self.img.shape[0] + dxy, :, :] = self.img
        return mask

    def img_handle(self,img=None):
        if np.any(img):
            self.img=img

        self.img = cv2.cvtColor(self.img, cv2.COLOR_BGR2HSV)

        cv2.GaussianBlur(self.img, [5, 5], 0)

        self.img = cv2.inRange(self.img, self.lowHSV, self.highHSV)

        kernel = np.ones([3, 3], dtype=np.uint8)
        self.img = cv2.morphologyEx(self.img, cv2.MORPH_CLOSE, kernel, iterations=1)
        kernel = np.ones([3, 3], dtype=np.uint8)
        self.img = cv2.morphologyEx(self.img, cv2.MORPH_DILATE, kernel, iterations=1)

        contours, num = cv2.findContours(self.img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            lenth = cv2.arcLength(contour, True)
            if self.area_max >area > self.area_min and self.lenth_max >lenth > self.lenth_min:

                epsilon = 0.02 * cv2.arcLength(contour, True)
                self.allpoint = cv2.approxPolyDP(contour, epsilon, True)

                self.allpoint = self.allpoint.reshape(len(self.allpoint), 2)
                self.allpoint = np.array(self.allpoint, dtype=np.int32)
                if self.drawtype==0:

                    b = random.randint(0, 255)
                    g = random.randint(0, 255)
                    r = random.randint(0, 255)

                    cv2.polylines(self.output_img, [self.allpoint], True, [b, g, r], 4, 16)
        return self.img


    def get_distance(self, pt1, pt2):
        distance = ((pt2[0] - pt1[0]) ** 2 + (pt2[1] - pt1[1]) ** 2) ** (0.5)
        return distance

    def detect(self):
        num = 0
        if np.any(self.allpoint):
            maxindex  = np.argmax(self.allpoint, axis=0)
            for point in self.allpoint:
                distance = self.get_distance(self.allpoint[maxindex [1], :], point)
                if distance > self.distance:
                    if self.drawtype ==1:

                        b = random.randint(0, 255)
                        g = random.randint(0, 255)
                        r = random.randint(0, 255)

                        cv2.line(self.output_img,self.allpoint[maxindex [1],:],point,[b, g, r],4,16)
                    num += 1
            if num == 1:
                cv2.putText(self.output_img, 'one', [10, 50], cv2.FONT_HERSHEY_SIMPLEX, 2, [0, 0, 255], thickness=4)
                return '一'
            elif num == 2:
                cv2.putText(self.output_img, 'two', [10, 50], cv2.FONT_HERSHEY_SIMPLEX, 2, [0, 0, 255], thickness=4)
                return '二'
            elif num == 3:
                cv2.putText(self.output_img, 'three', [10, 50], cv2.FONT_HERSHEY_SIMPLEX, 2, [0, 0, 255], thickness=4)
                return '三'
            elif num == 4:
                cv2.putText(self.output_img, 'four', [10, 50], cv2.FONT_HERSHEY_SIMPLEX, 2, [0, 0, 255], thickness=4)
                return '四'
            elif num == 5:
                cv2.putText(self.output_img, 'five', [10, 50], cv2.FONT_HERSHEY_SIMPLEX, 2, [0, 0, 255], thickness=4)
                return '五'

    def get_hand(self,img):
        self.img = img
        if self.img.shape[0] != 480 and self.img.shape[1] != 640:
            self.img = self.resize_img([640,480,3])
        self.output_img=np.copy(self.img)
        last_img=self.img_handle()
        num=self.detect()
        return self.output_img,last_img,num

class GUI:
    def __init__(self):
        #
        self.hand=Img_handle(20000,1000,280)

        self.num=''
        self.video=''
        self.after=''
        self.file=['.mp4','.png','jpg']
        self.file_name=''

        self.root=tkinter.Tk()
        self.root.geometry('1000x700')
        self.root.title('手势识别')
        self.root.resizable(width=False,height=False)

        self.Img1label=tkinter.Label(self.root,text='',bg='white',bd=10)
        self.Img1label.place(x=200+40+100,y=20,width=640,height=480)

        self.Img2label=tkinter.Label(self.root,text='',bg='white',bd=10)
        self.Img2label.place(x=20,y=20+50+20+50+20+50+20,width=250,height=400)

        self.bt1=tkinter.Button(self.root,text='选择文件',command=self.path_get,font=('宋体',20),bg='green',bd=10)
        self.bt1.place(x=20,y=20,width=250,height=50)

        self.bt2=tkinter.Button(self.root,text='打开',command=self.img_open,font=('宋体',20),bg='blue',bd=10)
        self.bt2.place(x=20,y=20+50+20,width=250,height=50)

        self.bt3=tkinter.Button(self.root,text='打开摄像头',command=self.video_change,font=('宋体',20),bg='white',bd=10)
        self.bt3.place(x=20,y=20+50+20+50+20,width=250,height=50)

        self.string=tkinter.StringVar(self.root,value='')
        self.str_output=tkinter.Entry(self.root,textvariable=self.string,state='readonly',font=('宋体',38),bg='white',bd=10)
        self.str_output.place(x=200+40+100,y=20*3+480,width=640,height=140)

        #orient设置朝向
        #tickinterval设置刻度
        #resolution设置步长
        self.intvar = tkinter.IntVar(self.root)
        self.scale=tkinter.Scale(self.root,label='距离阈值',from_=0,to=800,\
        resolution=1,orient=tkinter.HORIZONTAL,tickinterval=200,variable=self.intvar,bg='white',bd=10)
        self.scale.place(x=20,y=700-80,width=250)
        self.get_scale()

    def video_change(self):
        if self.video:
            self.video.release()
        self.video = cv2.VideoCapture(0)
        if self.after:
            self.root.after_cancel(self.after)
        self.video_open()

    def video_open(self):
        res,img=self.video.read()
        if res == True and np.any(img):
            img1,img2,self.num=self.hand.get_hand(img)
            self.img1_show(img1)
            self.img2_show(img2)
        self.after=self.root.after(10,self.video_open)

    def img_open(self):
        if not self.file_name:
            showerror(title='警告', message='请选择视频或者图片')
        elif self.file[0] in self.file_name:
            if self.video:
                self.video.release()
            self.video = cv2.VideoCapture(self.file_name)
            if self.after:
                self.root.after_cancel(self.after)
            self.video_open()
        else:
            if self.video:
                self.video.release()
            img=cv2.imread(self.file_name)
            img1,img2,self.num=self.hand.get_hand(img)
            self.img1_show(img1)
            self.img2_show(img2)

    def path_get(self):
        self.file_name=filedialog.askopenfilename()
        num=0
        for path in self.file:
            if path not in self.file_name:
                    num+=1
        if num==3:
            showerror(title='警告',message='请选择视频或者图片')

    def get_scale(self):
        distance=self.intvar.get()
        self.hand.change_distance(distance)
        self.string.set('手势检测结果为%s'%(self.num))
        self.root.after(10, self.get_scale)

    def img1_show(self,img):
        img=cv2.cvtColor(img,cv2.COLOR_BGR2RGBA)
        img=fromarray(img)
        img=PhotoImage(img)
        self.Img1label.image=img
        self.Img1label['image']=img

    def img2_show(self,img):
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        img = self.hand.resize_img([250, 400,3], img)
        img=cv2.cvtColor(img,cv2.COLOR_BGR2RGBA)
        img=fromarray(img)
        img=PhotoImage(img)
        self.Img2label.image=img
        self.Img2label['image']=img

    def open(self):
        showerror('注意',message='使用时先将距离阈值滑块调至273左右，再根据实际情况调节,最好带口罩识别防止误识别')
        self.root.mainloop()

    def close(self):
        if self.video:
            self.video.release()


GUI().open()
GUI().close()
