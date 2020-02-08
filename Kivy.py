from libdw import pyrebase
from kivy.app import App
from kivy.properties import StringProperty
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.image import Image
from kivy.graphics.vertex_instructions import Rectangle
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.lang import Builder
from kivy.utils import rgba
import numpy as np
from sklearn.svm import SVR
import matplotlib.pyplot as plt
from joblib import dump, load
import csv
import datetime

###############################################################################
# Firebase Settings

url = "https://dw-1d-12da9.firebaseio.com/"
apikey = "AIzaSyBNDNhK3ReJ1574poKc-C7ATXAgw5sMSAU"

config = {
    "apiKey": apikey,
    "databaseURL": url,
  }
firebase = pyrebase.initialize_app(config)
db = firebase.database()
root = db.child("/").get()

##############################################################################

Window.clearcolor = (0, 0, 0, 1)


class MyButton(Button):
    background_normal = ''
    color = 0,0,0,1
    halign = 'center'
    

class ScreenManagement(ScreenManager):
    pass

class Screen1(Screen):
    pass

class Screen2(Screen):
    
    # Initialise
    def __init__(self, **kwargs):
        super(Screen2, self).__init__(**kwargs)
        self.avail = "0"
        
        # Retrieve state of washers and dryers from firebase
        self.states = { \
        "w1" : db.child("Washer 1").get().val(),\
        "w2" : db.child("Washer 2").get().val(),\
        "w3" : "Available",\
        "w4" : "Available",\
        "w5" : "Available",\
        "w6" : "Available",\
        "w7" : "Available",\
        "w8" : "Available",\
        "w9" : "Available",\
        "w10" : "Available",\
        "w11" : "Available",\
        "d1" : "Available",\
        "d2" : "Available",\
        "d3" : "Available",\
        "d4" : "Available",\
        "d5" : "Available",\
        "d6" : "Available",\
        }

        # Colour of the washer and dryer display changes depending on whether
        # availability (red or green)
        self.colors = {}
        for i in self.states:
            if self.states[i] == "Not Available":
                button_color = (242/255, 102/255, 38/255, 1)
    
            elif self.states[i] == "Available":
                button_color = (0.5, 1., 0.5, 1.0)
    
            self.colors[i] = button_color
        
        
    
    # Refresh Data    
    def load_data(self):
        print("Refreshing data...")
        
        #retrieve state of washers and dryers from firebase
        self.states = { \
        "w1" : db.child("Washer 1").get().val(),\
        "w2" : db.child("Washer 2").get().val(),\
        "w3" : "Available",\
        "w4" : "Available",\
        "w5" : "Available",\
        "w6" : "Available",\
        "w7" : "Not Available",\
        "w8" : "Available",\
        "w9" : "Available",\
        "w10" : "Available",\
        "w11" : "Available",\
        "d1" : "Available",\
        "d2" : "Not Available",\
        "d3" : "Available",\
        "d4" : "Available",\
        "d5" : "Available",\
        "d6" : "Available",\
        }
        
        # Colour of the washer and dryer display changes depending on whether
        # availability (red or green)
        self.colors = {}
        for i in self.states:
            if self.states[i] == "Not Available":
                button_color = (242/255, 102/255, 38/255, 1)
    
            elif self.states[i] == "Available":
                button_color = (0.5, 1., 0.5, 1.0)
    
            self.colors[i] = button_color
        
        self.update = {}
        
        self.ids.w1.background_color = self.colors["w1"]
        self.ids.w1.text ='Washer 1\n'+ self.states["w1"]

        self.ids.w2.background_color = self.colors["w2"]
        self.ids.w2.text ='Washer 2\n'+ self.states["w2"]
        self.update_avail()
        
        
        
    # Retrieve data from csv datafile    
    def get_data(self,csv_file):
        X = []
        y = []
        
        # Read csv datafile
        with open(csv_file, 'r',encoding='utf-8') as f: 
            reader = csv.reader(f)
            for row in reader:
                try:
                    X.append(int(row[0]))
                    y.append(int(row[1]))
                except:
                    pass
        X = np.array(X)
        X = np.reshape(X,(-1,1))
        y = np.array(y)
        y = y/2
        
        # Return X and y axis in numpy array
        return X,y  
    
    
    
    # Train and make model of data
    def make_model(self,csv_file):
        X,y = self.get_data(csv_file)
        
        # Use a Support Vector Regression (SVR) model
        svr_rbf = SVR(kernel = 'rbf', C = 10, gamma = 0.1, epsilon = .1)
        model = svr_rbf.fit(X, y)
    
        # Save model to .joblib file
        name = csv_file.split(".")
        dump(model, f'{name[0]}.joblib') 
    
        return model
    
    
    
    # Update Percentage Availability
    def update_avail(self):
        # Get current time and put it into 2D numpy array
        currentDT = datetime.datetime.now()
        hournow = np.array(currentDT.hour)
        hournow = hournow.reshape(-1,1)
        
        # Train and model data
        model = self.make_model('thursday_data.csv')
        model = load('thursday_data.joblib')
        X,y = self.get_data("thursday_data.csv")
        
        # Plot graph 
        plot_graph(X,y)
        
        # Check that self.avail is a ratio between 0 and 1
        avail = round(model.predict(hournow)[0],3)
        print(avail)
        self.avail = str(avail)
        print(self.avail)
        if avail < 0:
            self.avail = 0
        elif avail >1:
            self.avail = 1
            
        # Create new display to show percentage availability for next hour
        self.ids.write_here.text = f'Next Hour Availability: {self.avail}'



# Plot Support Vector Regression graph of X against y
def plot_graph(X,y):
    lw = 2
    svr_rbf = SVR(kernel='rbf', C=10, gamma=0.1, epsilon=.1)
    svrs = [svr_rbf]
    kernel_label = ['RBF']
    model_color = ['m']

    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(15, 10), sharey=True)
    for ix, svr in enumerate(svrs):
        axes[ix].plot(X, svr.fit(X, y).predict(X), color=model_color[ix], lw=lw,
                    label='{} model'.format(kernel_label[ix]))
        axes[ix].scatter(X[svr.support_], y[svr.support_], facecolor="none",
                        edgecolor=model_color[ix], s=50,
                        label='{} support vectors'.format(kernel_label[ix]))
        axes[ix].scatter(X[np.setdiff1d(np.arange(len(X)), svr.support_)],
                        y[np.setdiff1d(np.arange(len(X)), svr.support_)],
                        facecolor="none", edgecolor="k", s=50,
                        label='other training data')
        axes[ix].legend(loc='upper center', bbox_to_anchor=(0.5, 1.1),
                        ncol=1, fancybox=True, shadow=True)

    fig.text(0.5, 0.04, 'data', ha='center', va='center')
    fig.text(0.06, 0.5, 'target', ha='center', va='center', rotation='vertical')
    fig.suptitle("Support Vector Regression", fontsize=14)
    plt.show()
        
        
        
# Layout of kivy is done in Kivy language, with the file named Main.kv
presentation = Builder.load_file("Main.kv")



# Set background image of main page
class MainApp(App):
    
    # Set background image file 
    wimg = Image(source='Graduate-Housing.jpg')
    
    
    def build(self):
        self.root = root
        
        return presentation
  

if __name__ == "__main__":
  MainApp().run()
