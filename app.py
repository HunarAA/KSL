from typing import List

import cv2
import torch
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.colors as mcolors
from PIL import Image
from streamlit_webrtc import VideoTransformerBase, webrtc_streamer
from config import CLASSES, WEBRTC_CLIENT_SETTINGS

st.set_page_config(
    page_title="سیستەمی ناسینەوەی زمانی ئاماژەی کوردی",
)

st.markdown("<h1 style='text-align: center; font-family: Rabar_022; color: rgba(31, 72, 238, 0.899);'>سیستەمی ناسینەوەی زمانی ئاماژەی کوردی</h1>", unsafe_allow_html=True)

#region Functions
# --------------------------------------------
# M - 10
model_path1 = 'best_m_10.pt'
#  S - 10
model_path2 = 'best_s_10.pt'
#  M - 21
model_path3 = 'best_m_21.pt'
# S - 21
model_path4 = 'D:/RealTimeObjectDetection/hunar_yolo/yolov5_m_ws9/yolov5/runs/train/exp/weights/best.pt'
@st.cache(max_entries=2)
def get_yolo5(model_type='M-10'):
    if model_type=='M-10':
        return torch.hub.load('ultralytics/yolov5', 'custom', path=model_path1, force_reload=True)
    elif model_type=='M-21':
        return torch.hub.load('ultralytics/yolov5', 'custom', path=model_path3, force_reload=True)
    elif model_type=='S-10':
        return torch.hub.load('ultralytics/yolov5', 'custom', path=model_path2, force_reload=True)

@st.cache(max_entries=10)
def get_preds(img : np.ndarray) -> np.ndarray:
    return model([img]).xyxy[0].numpy()

def get_colors(indexes : List[int]) -> dict:
    to_255 = lambda c: int(c*255)
    tab_colors = list(mcolors.TABLEAU_COLORS.values())
    tab_colors = [list(map(to_255, mcolors.to_rgb(name_color))) 
                                                for name_color in tab_colors]
    base_colors = list(mcolors.BASE_COLORS.values())
    base_colors = [list(map(to_255, name_color)) for name_color in base_colors]
    rgb_colors = tab_colors + base_colors
    rgb_colors = rgb_colors*5

    color_dict = {}
    for i, index in enumerate(indexes):
        if i < len(rgb_colors):
            color_dict[index] = rgb_colors[i]
        else:
            color_dict[index] = (255,0,0)

    return color_dict

def get_legend_color(class_name : int):
    index = CLASSES.index(class_name)
    color = rgb_colors[index]
    return 'background-color: rgb({color[0]},{color[1]},{color[2]})'.format(color=color)

class VideoTransformer(VideoTransformerBase):
    def __init__(self):
        self.model = model
        self.rgb_colors = rgb_colors
        self.target_class_ids = target_class_ids

    def get_preds(self, img : np.ndarray) -> np.ndarray:
        return self.model([img]).xyxy[0].numpy()

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        result = self.get_preds(img)
        result = result[np.isin(result[:,-1], self.target_class_ids)]
        
        for bbox_data in result:
            xmin, ymin, xmax, ymax, _, label = bbox_data
            p0, p1, label = (int(xmin), int(ymin)), (int(xmax), int(ymax)), int(label)
            img = cv2.rectangle(img,p0, p1, self.rgb_colors[label], 2)
            img = cv2.putText(img, str(CLASSES[label]), (p1[0] - 100, p0[1]-20),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, rgb_colors[label], 1)

        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

#endregion


#region Load model
# ---------------------------------------------------

model_type = st.sidebar.selectbox('جۆری مۆدێل',('M-21', 'M-10', 'S-10'),
    index=1,format_func=lambda s: s.upper())

with st.spinner('Loading the model...'):
    model = get_yolo5(model_type)
st.success('Loading the model.. Done!')
#endregion

# UI elements
# ----------------------------------------------------

#sidebar
prediction_mode = st.sidebar.radio(
    "ناسینەوە لە ڕێگەی",
    ('وێنە', 'وێب کام'),
    index=0)
    
classes_selector = st.sidebar.multiselect('ئاماژەکان دیاری بکە', 
                                        CLASSES, default='Ruberru')
all_labels_chbox = st.sidebar.checkbox('هەموو ئاماژەکان', value=False)

# Prediction section
# ---------------------------------------------------------
if all_labels_chbox:
    target_class_ids = list(range(len(CLASSES)))
elif classes_selector:
    target_class_ids = [CLASSES.index(class_name) for class_name in classes_selector]
else:
    target_class_ids = [0]

rgb_colors = get_colors(target_class_ids)
detected_ids = None

col1,col2 = st.beta_columns([3,1])

with col1:
    if prediction_mode == 'وێنە':

        uploaded_file = st.file_uploader(
            "وێنەیەک بهێنە",
            type=['png', 'jpg', 'jpeg'])

        if uploaded_file is not None:

            bytes_data = uploaded_file.getvalue()
            file_bytes = np.asarray(bytearray(bytes_data), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            result = get_preds(img)
            result_copy = result.copy()
            result_copy = result_copy[np.isin(result_copy[:,-1], target_class_ids)]
            

            detected_ids = []
            img_draw = img.copy().astype(np.uint8)
            for bbox_data in result_copy:
                xmin, ymin, xmax, ymax, _, label = bbox_data
                p0, p1, label = (int(xmin), int(ymin)), (int(xmax), int(ymax)), int(label)
                img_draw = cv2.rectangle(img_draw, p0, p1, rgb_colors[label], 15)
                img_draw = cv2.putText(img_draw, str(CLASSES[label]), (p1[0] - 300, p0[1]-20),
                    cv2.FONT_HERSHEY_DUPLEX, 3, rgb_colors[label], 2)
                detected_ids.append(label)
            
            st.image(img_draw, use_column_width=True)

    elif prediction_mode == 'وێب کام':
        
        ctx = webrtc_streamer(
            key="example", 
            video_transformer_factory=VideoTransformer,
            client_settings=WEBRTC_CLIENT_SETTINGS,)

        if ctx.video_transformer:
            ctx.video_transformer.model = model
            ctx.video_transformer.rgb_colors = rgb_colors
            ctx.video_transformer.target_class_ids = target_class_ids
with col2:
    detected_ids = set(detected_ids if detected_ids is not None else target_class_ids)
    labels = [CLASSES[index] for index in detected_ids]
    legend_df = pd.DataFrame({'ئاماژەکان': labels})
    st.dataframe(legend_df.style.applymap(get_legend_color))



if model_type or classes_selector or all_labels_chbox or prediction_mode:
    st.markdown(
        """
    <style>
        @font-face {
        font-family: 'Rabar_022';
        }

    html, body, [class*="css"]  {
    font-family: 'Rabar_022';
    font-size: 15px;
    font-weight: 600;
    }
    </style>

    """,
        unsafe_allow_html=True,
    )