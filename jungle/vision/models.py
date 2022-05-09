import cv2
import numpy as np
from requests import post
from django.db import models
from google.cloud import vision
from logging import getLogger
from base64 import b64encode, b64decode

from commonlib.secretmanager import get_secret
from jungle.settings import BASE_DIR

logger = getLogger("vision")

"""
Tensflow Keras loading inside class
Contains two different types of models
Django Model - VisionDB to host images
AI-Vision Models, is ai
"""

class VisionDB(models.Model):
    userimage = models.ImageField("Upload a picture", upload_to ="vision/")
    userdesc = models.CharField("User Description", max_length=1023, blank=True)
    aimodel = models.CharField("Select a vision model", max_length=100, choices=[
        ("Web API" , (
            ("AZ", "Azure Congnitive"),
            ("GCP", "Google Cloud Vision"),
        )),
        ("Local", (
            ("mn", "Mobilenet"), 
            ("yolov3", "YOLO-416"),
            ("yolov3-tiny", "YOLO-tiny"),
        )),
        ("Special-3-step", (
            ("husky", "Haar + EfficientNet + MobileNetV3 (slow)"),
        )),
    ])
    outjson = models.TextField("Value (json as str)", max_length=65535, blank=True)
    timestamp = models.DateTimeField(auto_now=True)


def get_img_bytes(source, max_width=900.0):
    # image_data = open(source, "rb").read()
    # resize if needed
    img = cv2.imread(source)
    if img.shape[1] > max_width:
        print (img.shape)
        height = img.shape[0] * max_width / img.shape[1] 
        img = cv2.resize(img, (int(max_width), int(height)), interpolation = cv2.INTER_AREA)

    _, frame_buff = cv2.imencode('.jpg', img) 
    image_data = b64encode(frame_buff).decode("UTF-8")

    return img, image_data


class GCPDetector:
    def __init__(self):
        self.client = vision.ImageAnnotatorClient()

    def readImage(self, source, display=False):
        img, image_data = get_img_bytes(source)

        analysis = self.client. \
            object_localization(image=vision.Image(content=image_data)). \
            localized_object_annotations
        color_map = {}
        for objname in set([obj.name for obj in analysis]):
            color_map[objname] = np.random.uniform(0, 255, size=3)

        hh, ww, _ = img.shape
        for obj in analysis:
            label = obj.name
            confidence = obj.score
            color = color_map[obj.name]
            pts = [[vertex.x * ww, vertex.y * hh] for vertex in obj.bounding_poly.normalized_vertices]
            pts = np.array(pts, np.int32)
            cv2.putText(img, f"{label} ({confidence:.2f})", (pts[0][0], pts[0][1]-10), cv2.FONT_HERSHEY_PLAIN, 1, color, 2)
            cv2.polylines(img, [pts.reshape((-1, 1, 2))], True, color, 2)

        if type(source) == str and display:
            cv2.imshow("Google Cloud Vision", img)
            cv2.waitKey(-1)
        if not display:
            return img, analysis
        return img



class AZDetector:

    def __init__(self, params={'visualFeatures': 'Description,Brands,Objects', 'details': 'Celebrities,Landmarks'}):
        # Categories, Color, ImageType can be added
        self.params = params
        self.azkey = get_secret("ycrawl-credentials", as_json=True)["AZURE_CV"]
        self.endpoint = "https://yyyazurecv.cognitiveservices.azure.com/vision/v3.2/analyze"

    def readImage(self, source, display=False):
        img, image_data = get_img_bytes(source)
        image_data = b64decode(image_data)
  
        # https://westus.dev.cognitive.microsoft.com/docs/services/computer-vision-v3-2/operations/56f91f2e778daf14a499f21b
        response = post(
            self.endpoint,
            headers={'Ocp-Apim-Subscription-Key': self.azkey, 'Content-Type': 'application/octet-stream'},
            params=self.params,
            data=image_data,
        )
        response.raise_for_status()
        analysis = response.json()
        color_map = {}
        for objname in set([obj["object"] for obj in analysis["objects"]]):
            color_map[objname] = np.random.uniform(0, 255, size=3)

        # use cv2 to display pic
        title = analysis["description"]["captions"][0]['text'].capitalize()
        for obj in analysis["objects"]:
            x,y,w,h = obj["rectangle"].values()
            label = obj["object"]
            confidence = obj["confidence"]
            color = color_map[label]
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
            cv2.putText(img, f"{label} ({confidence:.2f})", (x, y-10), cv2.FONT_HERSHEY_PLAIN, 1, color, 2)

        if type(source) == str and display:
            cv2.imshow("Azure Cognitive", img)
            cv2.waitKey(-1)
        if not display:
            return img, analysis
        return img



def get_cocos(shortname="coco.names", append0 = True):
    with open(f"{BASE_DIR}/vision/opencv_model/{shortname}", "r") as f:
        classes_from_file = f.read().splitlines()
    classes = ["NA"] + classes_from_file if append0 else classes_from_file
    # fixed colors
    colors = np.random.uniform(0, 255, size=(len(classes), 3))

    return classes, colors


class BaseDetector:

    def __init__(self, model_selection="mobilenet"):
        self.classes, self.colors = get_cocos()            

        if model_selection.lower() == "mobilenet":
            self.net = cv2.dnn_DetectionModel(
                f"{BASE_DIR}/vision/opencv_model/frozen_inference_graph.pb",
                f"{BASE_DIR}/vision/opencv_model/ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"
            )
            self.net.setInputSize(320, 320)
            self.net.setInputScale(1./127.5)
            self.net.setInputMean((127.5, 127.5, 127.5))
            self.net.setInputSwapRB(True)
            
    def readImage(self, source, display=False):
        img = cv2.imread(source) if type(source) == str else source
        class_ids, confidences, bndboxes = self.net.detect(img, confThreshold = 0.4)
        nms_boxes = cv2.dnn.NMSBoxes(list(bndboxes), confidences, score_threshold=0.5, nms_threshold=0.2)
        
        outjson = {"model": "mobilenet", "objects": []}
        for box_id in nms_boxes:
            confidence = confidences[box_id]
            label = self.classes[class_ids[box_id]]
            color = self.colors[class_ids[box_id]]
            x,y,w,h = bndboxes[box_id]
            cv2.rectangle(img, (x,y), (x+w, y+h), color=color, thickness=2)
            cv2.putText(img, f"{label} ({confidence:.2f})", (x, y-10), cv2.FONT_HERSHEY_PLAIN, 1, color, 2)
            outjson["objects"].append({"label": label, "confidence": confidence, "bndbox": [x,y,w,h]})

        if type(source) == str and display:
            cv2.imshow("MobileNet", img)
            cv2.waitKey(-1)
        if not display:
            return img, outjson
        return img

    def readVideo(self, video_src):
        cap = cv2.VideoCapture(video_src)
        flag, img = cap.read()

        while flag:
            cv2.imshow("MobileNet", self.readImage(img))
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == 32:
                cv2.waitKey(-1)

            flag, img = cap.read()

        cap.release()
        cv2.destroyAllWindows() 




class YoloDetector:

    def __init__(self, model_selection="yolov3-tiny"):
        # paths to files
        self.classes, self.colors = get_cocos("yolov3.coco.names", False)

        self.net = cv2.dnn.readNet(
            f"{BASE_DIR}/vision/opencv_model/{model_selection}.weights", 
            f"{BASE_DIR}/vision/opencv_model/{model_selection}.cfg"
        )
        self.imgsize = (416, 416)
        layer_names = self.net.getLayerNames()
        # print(len(layer_names), layer_names)
        self.output_layers = [layer_names[i - 1] for i in self.net.getUnconnectedOutLayers()]

    def readImage(self, source, display=False):
        img = cv2.imread(source) if type(source) == str else source
        height, width, _ = img.shape
        self.net.setInput(
            cv2.dnn.blobFromImage(img, 0.00392, self.imgsize, (0, 0, 0), True, crop=False)
        )
        outs = self.net.forward(self.output_layers)

        # Showing informations on the screen
        class_ids, confidences, bndboxes = [], [], []
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.5:
                    center_x, center_y = int(detection[0] * width), int(detection[1] * height)
                    w, h = int(detection[2] * width), int(detection[3] * height)
                    x, y = int(center_x - w / 2), int(center_y - h / 2)
                    bndboxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)

        nms_boxes = cv2.dnn.NMSBoxes(bndboxes, confidences, 0.5, 0.4)

        outjson = {"model": "mobilenet", "objects": []}
        for box_id in nms_boxes:
            x, y, w, h = bndboxes[box_id]
            label = str(self.classes[class_ids[box_id]])
            confidence = confidences[box_id]
            color = self.colors[box_id]
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
            cv2.putText(img, f"{label} ({confidence:.2f})", (x, y-10), cv2.FONT_HERSHEY_PLAIN, 1, color, 2)
            outjson["objects"].append({"label": label, "confidence": confidence, "bndbox": [x,y,w,h]})

        if type(source) == str and display:
            cv2.imshow("Yolo", img)
            cv2.waitKey(-1)
        if not display:
            return img, outjson
        return img
            

    def readVideo(self, video_src):
        cap = cv2.VideoCapture(video_src)
        flag, img = cap.read()

        while flag:
            cv2.imshow("Yolo", self.readImage(img))
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord("q"):
                break
            elif key == 32:
                cv2.waitKey(-1)

            flag, img = cap.read()
            
        cap.release()
        cv2.destroyAllWindows() 



#   _____              ___ _                          
#  |_   _|_ __ _____  / __| |_ ___ _ __ _ __  ___ _ _ 
#    | | \ V  V / _ \ \__ \  _/ -_) '_ \ '_ \/ -_) '_|
#    |_|  \_/\_/\___/ |___/\__\___| .__/ .__/\___|_|  
#                                 |_|  |_|            

# face masking
class FaceAnonymizer:
    def __init__(self):
        # https://github.com/opencv/opencv/tree/4.x/data/haarcascades
        self.face_cascade = cv2.CascadeClassifier(f"{BASE_DIR}/vision/opencv_model/face.xml")
    
    def detect_face_tensor(self, tensor, blur=0):
        # Convert into grayscale
        gray = cv2.cvtColor(tensor, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        if blur > 0:
            for (x, y, w, h) in faces:
                face_area = tensor[y:(y+h), x:(x+w)]
                # blur size must be odd number
                blur_size = (2*int(w/blur/2) + 1, 2*int(h/blur/2) + 1)
                tensor[y:(y+h), x:(x+w)] = cv2.GaussianBlur(face_area, blur_size, 0)
        
        return tensor, faces


# object detector
class HuskyLiteDetector():
    def __init__(self, threshold = 0.2):
        import tensorflow as tf
        self.threshold = threshold
        self.names = ['Kali', 'Keke', 'Tati', 'Tonti']
        self.interpreter = tf.lite.Interpreter(model_path=f"{BASE_DIR}/vision/opencv_model/husky.tflite")
        self.interpreter.allocate_tensors() 
        self.input_size = self.interpreter.get_input_details()[0]['shape'][[2,1]]
        self.input_index = self.interpreter.get_input_details()[0]['index']


        sorted_indices = sorted([x['index'] for x in self.interpreter.get_output_details()])
        self.i_box, self.i_cls, self.i_score = sorted_indices[0:3] # count is not used

    def predict_tensor(self, tensor):
        image_height, image_width, _ = tensor.shape
        tensor = cv2.resize(tensor, self.input_size)
        tensor = np.expand_dims(tensor, axis=0)
        
        # run model
        self.interpreter.set_tensor(self.input_index, tensor)
        self.interpreter.invoke()

        # assemble output
        boxes = np.squeeze(self.interpreter.get_tensor(self.i_box))
        classes = np.squeeze(self.interpreter.get_tensor(self.i_cls))
        scores = np.squeeze(self.interpreter.get_tensor(self.i_score))

        results = []
        for i, box in enumerate(boxes):
            y_min, x_min, y_max, x_max = box
            results.append({
                "bounding_box": {
                    "top": int(y_min * image_height),
                    "left": int(x_min * image_width),
                    "bottom": int(y_max * image_height),
                    "right": int(x_max * image_width),
                },
                "class_id": int(classes[i]),
                "class": self.names[int(classes[i])],
                "score": scores[i]
            })
        return [r for r in results if r["score"] > self.threshold]

    def predict(self, image_path):
        tensor = cv2.imread(image_path)
        return self.predict_tensor(tensor)



# classifier
class HuskyNamer():
    
    def __init__(self):
        from keras.models import load_model
        self.names = ['Kali', 'Keke', 'Tati', 'Tonti']
        self.input_size = 224, 224
        self.model = load_model(f"{BASE_DIR}/vision/opencv_model/huskynames.mns.hdf5")
        self.model.compile(optimizer='rmsprop', loss="categorical_crossentropy", metrics=["accuracy"])
        
    def predict_tensor(self, tensor):
        tensor = cv2.resize(tensor, self.input_size)
        tensor = np.expand_dims(tensor, axis=0)
        classes = self.model.predict(np.vstack([tensor]))[0]
        class_id = np.argmax(classes)

        return {"class": self.names[class_id], "class_id": class_id, "score": classes[class_id]}

    def predict(self, image_path):
        tensor = cv2.imread(image_path)
        return self.predict_tensor(tensor)



class HuskyInTwoSteps():
    def __init__(self):
        self.face = FaceAnonymizer()
        self.huskydetector = HuskyLiteDetector()
        self.huskynamer = HuskyNamer()

    def readImage(self, source, display=False):
        image_tensor = cv2.imread(source) if type(source) == str else source
        
        # detector step:
        image_tensor, _ = self.face.detect_face_tensor(image_tensor, blur=3)
        results = self.huskydetector.predict_tensor(image_tensor)
        # using classifier to enhance results
        for res in results:
                box = res["bounding_box"]
                object_tensor = image_tensor[box["top"]:box["bottom"], box["left"]:box["right"]]
                res2 = self.huskynamer.predict_tensor(object_tensor)
                res["class2"], res["score2"] = res2["class"], res["score"]

        # visualize
        for res in results:
                box = res["bounding_box"]
                cv2.rectangle(image_tensor, (box["left"], box["top"]), (box["right"], box["bottom"]), (0,0,255), 3)
                result_text = f"{res['class2']} {res['score2']} (was {res['class']})"
                text_location = (10 + box["left"], 20 + box["top"])
                cv2.putText(image_tensor, result_text, text_location, cv2.FONT_HERSHEY_PLAIN, 1, (0,0,255), 1)

        if type(source) == str and display:
            cv2.imshow("Husky in 3 steps", image_tensor)
            cv2.waitKey(-1)
        if not display:
            return image_tensor, results
        return image_tensor

