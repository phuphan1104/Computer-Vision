import sys
from PyQt5.uic import loadUi
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import time
import serial
import cv2
import numpy as np

# hiện thị giao diện
class MainWindow(QMainWindow):
    mouseSingnal = pyqtSignal(int,int)
    connectPortSignal = pyqtSignal(int,str,str,str,str)

    def __init__(self):
        super().__init__()
        loadUi('untitled.ui',self)
        self.Worker1 = Worker1()
        
        self.is_videoplaying = False
        self.textPortLabel = ''
        self.xPoin = ''
        self.yPoin = ''
        self.enableSer = None 
        

        self.timer1 = QTimer(self)
        self.timer1.start()
        self.timer1.timeout.connect(self.updateTime)
        self.timer1.timeout.connect(self.updatePort)

        self.pushButton.clicked.connect(self.EnablePort)
        self.DispushButton.clicked.connect(self.UnEnablePort)

        self.checkoutButton.clicked.connect(self.checkout)
        self.checkinButton.clicked.connect(self.checkin)
        self.VideoLabel.mousePressEvent = self.mouseClick
    # Hiển thị VideoLabel
    def ImageUpdateSlot(self, Image, x_pst, y_pst, x0,y0):
        self.xPoin = f'{x_pst}'
        self.yPoin = f'{y_pst}'
        if Image is not None:
            self.VideoLabel.setPixmap(QPixmap.fromImage(Image))
            self.VideoLabel.setScaledContents(True)
        else: 
            print('ko ket noi') 
    # Nhấn PushButton
    def checkin(self): 
        if self.is_videoplaying == False:
            self.Worker1.start()
            self.Worker1.ImageUpdate.connect(self.ImageUpdateSlot)
            self.is_videoplaying = True
        else:
            pass
    def checkout(self):
        if self.is_videoplaying == True :
            self.Worker1.ImageUpdate.disconnect(self.ImageUpdateSlot)
            self.Worker1.quit()
            self.VideoLabel.clear()
            self.is_videoplaying = False
        else:
            pass  
    # Phát hiện sự kiện kích chuột
    def mouseClick(self, event):
        x = event.x()
        y = event.y()
        if self.is_videoplaying == True :
            self.mouseSingnal.emit(x,y)
            self.mouseSingnal.connect(self.Worker1.receiveXY)
    # Hiển thị thời gian
    def updateTime(self):
        now_ = QDateTime.currentDateTime()
        curent_date = now_.date().toString('ddd, dd MMMM yyyy')
        curent_time = now_.time().toString('hh:mm:ss')
        self.DateLabel.setText(curent_date)
        self.TimeLabel.setText(curent_time)
    
    def EnablePort(self):
        self.enableSer = 1
        self.connectPortSignal.emit(self.enableSer,self.Port_comboBox.currentText(),self.Baud_comboBox.currentText(),
                                    self.Timeout_comboBox.currentText(),self.Bytesize_comboBox.currentText())
        self.connectPortSignal.connect(self.Worker1.receivedSER)
    def UnEnablePort(self):
        self.enableSer = 0
        self.connectPortSignal.emit(self.enableSer,'','','','') 
        self.connectPortSignal.connect(self.Worker1.receivedSER)
   
    def nhantextPortLabel(self,text):
        self.textPortLabel = text
        
    def updatePort(self):
        self.Worker1.guitextPortLabel.connect(self.nhantextPortLabel)
        self.PoinXLabel.setText(self.xPoin)
        self.PoinYLabel.setText(self.yPoin)
        self.ConnectLabel.setText(self.textPortLabel)
# luồng xử lý Cam
class Worker1(QThread):
    ImageUpdate = pyqtSignal(QImage,int,int,int,int)
    guitextPortLabel = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.ix = None
        self.iy = None
        self.s = False
        self.k = False

        
        self.is_openSerial = False
        self.ser = None
        self.com = None
        self.baud = None
        self.timeout = None
        self.bytesize = None
        self.enableSerial = None
        self.textPortLabel = None
    # mouseClick : nhận sự kiện chuột từ gui
    def receiveXY(self, x, y):
        self.ix = int(x*640/981)
        self.iy = int(y*480/731)
        print(self.ix,self.iy)
        self.s = True 
    # comPort: kết nối cổng serial
    def receivedSER(self,x, com, baud, timeout, bytesize):
        self.enableSerial = x
        self.com = com
        self.baud = baud
        self.timeout = timeout
        self.bytesize = bytesize
        if self.enableSerial:
            self.connectPort(com=self.com,baud=self.baud,timeout=self.timeout,bytesize=self.bytesize)
            print(self.enableSerial,self.com,self.baud,self.timeout,self.bytesize)
        else:
            self.disconnectPort()
            print(self.enableSerial,self.com,self.baud,self.timeout,self.bytesize)
    # Kết nối cổng COM
    def connectPort(self, com, baud, timeout, bytesize ):
        if self.ser is None and self.is_openSerial == False :
            self.ser = serial.Serial()
        if self.ser.is_open:
            self.ser.close()
        try:
            self.ser=serial.Serial(com)
            self.ser.close()
            self.ser.baudrate = int(baud)
            self.ser.timeout = float(timeout)
            self.ser.bytesize = int(bytesize)
            self.ser.open()
            self.is_openSerial = True
            self.textPortLabel = ('Đã kết nối cổng :\n' + self.ser.port + f'/{self.ser.baudrate}/{self.ser.timeout}/{self.ser.bytesize}')
            self.guitextPortLabel.emit(self.textPortLabel)
        except serial.serialutil.SerialException:
            self.textPortLabel = ('Error, kiểm tra cổng COM')
            self.guitextPortLabel.emit(self.textPortLabel)
    # Ngắt Kết nối cổng COM
    def disconnectPort(self):
        if self.ser is not None and self.is_openSerial == True:
            self.ser.close()
            self.ser = None
            self.com = None
            self.baud = None
            self.timeout = None
            self.bytesize = None
            self.enableSerial = None
            self.is_openSerial = False
            self.textPortLabel = ('Đã ngắt kết nối')
            self.guitextPortLabel.emit(self.textPortLabel)
        else:
            pass  
    # Gửi dữ liệu 
    def guidata(self,x,y,x0,y0):
        if self.ser is not None and self.is_openSerial == True:
            if self.ser.is_open:
                self.ser.write((f'{x},{y},{int(x0/2)},{int(y0/2)};').encode('utf-8'))
            if (self.ser.in_waiting):
                data_received = self.ser.readline().decode('utf-8')
                print("Received from Arduino:", data_received)
        else:
            pass
    # Nhận biết mục tiêu
    def detection_egde(self,img):
        kernel = np.ones((5,5),np.uint8)
        imgGray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        imgBlur = cv2.GaussianBlur(imgGray,(7,7),0)
        imgCanny = cv2.Canny(imgBlur,threshold1=30, threshold2=60)
        imgDialation = cv2.dilate(imgCanny,kernel,iterations=1)
        imgEroded = cv2.erode(imgDialation,kernel,iterations=1)
        return imgDialation	
    # Main
    def run(self):
        cap = cv2.VideoCapture(0) # đọc cam
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        while True:
            while True:
                success, img0 = cap.read()
                if not success:
                    break 
                img0=cv2.resize(img0,(640,480))
                img1 = cv2.flip(img0,1)
                img = img1
                imgEdge = self.detection_egde(img) 
                contours, _ = cv2.findContours(imgEdge, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for contour in contours:
                    if cv2.contourArea(contour) > 300 and cv2.contourArea(contour) < 1500   :  
                        x, y, w, h = cv2.boundingRect(contour) # tọa độ
                        cx = int (x+w/2)
                        cy = int(y+h/2)
                        region = [(x, y),(x,y+h) ,(x+w, y+h),(x+w,y)] 
                        distance = cv2.pointPolygonTest(np.array(region), (self.ix ,self.iy), False)
                        if distance > 0 and self.s == True:
                            self.ix, self.iy = cx,cy
                            self.s = False
                            self.k = True
                        cv2.circle(img,(int (x+w/2), int (y+h/2)), 2 , (0,0,255) ,3)
                        cv2.line(img , (int (x+w/2), y) , ( int (x+w/2),(y+h)) , (0,0,255))
                        cv2.line(img , (x,int(y+h/2)) , ((x+w),int (y+h/2)) , (0,0,255) )
                        cv2.rectangle(img, (x, y) , (x + w, y + h) , (0, 255, 0), 2)
                    #    Format QImage
                        current_frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        ConvertToQtFormat = QImage(current_frame.data, current_frame.shape[1], current_frame.shape[0], QImage.Format_RGB888)
                        Picture = ConvertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                        self.ImageUpdate.emit(Picture,0,0,0,0) 
                if self.k == True:
                    old_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
                    old_pts = np.array([[self.ix,self.iy]], dtype="float32").reshape(-1,1,2)
                    mask = np.zeros_like(img1)
                    print(self.ix,self.iy)
                    self.k = False
                    break         
            # bám theo dõi mục tiêu pp optical Flow
            while True:
                success2, frame2 = cap.read()
                if not success2:
                    break
                frame2=cv2.resize(frame2,(640,480))
                frame2 = cv2.flip(frame2,1)
                y_f, x_f = frame2.shape[0], frame2.shape[1]
                new_gray = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
                new_pts,status,err = cv2.calcOpticalFlowPyrLK(old_gray, 
                                    new_gray, 
                                    old_pts, 
                                    None, maxLevel=1,
                                    criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
                                                                    15, 0.08))
                
                cv2.circle(mask, (int(x_f/2),int(y_f/2)), 2, (0,0,255), 3)
                cv2.line(mask, (int (x_f/2),0), (int(x_f/2),y_f), (0,0,255))
                cv2.line(mask, (0,int(y_f/2)), (x_f,int (y_f/2)), (0,0,255))
                # toa do muc tieu
                x_pts, y_pts = int(new_pts[0][0][0]), int(new_pts[0][0][1])
                cv2.circle(frame2, (x_pts, y_pts), 2, (0,255,0), 3)
                # ve khoang cach 
                cv2.line(frame2, (int(x_f/2), int(y_f/2)), (x_pts, y_pts), (255,255,0))
                if x_pts < 0 or y_pts <0 or x_pts > x_f or y_pts > y_f  :
                    self.guidata(0,0,0,0)
                    print('break')
                else:
                    self.guidata(x_pts,y_pts,x_f,y_f)
                    print(x_pts,y_pts,x_f,y_f)
               
                if status.sum()>0:
                    old_pts = new_pts.copy()
                    old_gray = new_gray.copy()
                else:
                    break
                combined = cv2.addWeighted(frame2, 1, mask, 0.5, 0.1)
                #    Format QImage
                current_frame2 = cv2.cvtColor(combined, cv2.COLOR_BGR2RGB)
                ConvertToQtFormat = QImage(current_frame2.data, current_frame2.shape[1], current_frame2.shape[0], QImage.Format_RGB888)
                Picture2 = ConvertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                self.ImageUpdate.emit(Picture2,x_pts,y_pts,x_f,y_f) 

if __name__ == '__main__':
    App = QApplication(sys.argv)
    Root = MainWindow()
    Root.show()
    sys.exit(App.exec_())   