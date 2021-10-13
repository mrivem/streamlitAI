import os
import requests
from PIL import ExifTags, Image
import tensorflow as tf
from tensorflow import keras
from keras.models import load_model
import streamlit as st


MODEL_URL = 'https://inteligencia-artificial.s3.sa-east-1.amazonaws.com/best_model.h5'
MODEL_FILE = 'best_model.h5'

st.set_page_config(
    page_title="IA - Clasificador de frutas",
    page_icon="🍎"
)

st.write("# Clasificador de frutas")
st.markdown('Por Victor Matamala y Matias Rivera', unsafe_allow_html=True)
st.write("Este proyecto clasifica fotos de frutas utilizando una red neuronal convolucional.")
with st.expander("🧙 Haz click aca para saber mas sobre el modelo 🔮"):
    st.markdown("""
        <p>This is an introductory experiment on Artificial Inteligence. We trained a Convolutional Neural Network (CNN) with a dataset of 
        about 8,000 images of fruits. Our AI presents an accuracy of ~97% while classifying Apples, Bananas and Carambolas. 
        We used Google’s Colab as our platform for training this AI. The implementation was done using Tensorflow and Keras. 
        The training dataset was based on the <a href="https://www.kaggle.com/chrisfilo/fruit-recognition" target="_blank">Fruit Recognition</a>, 
        with approximately 3,000 images per fruit. 
        <p>10% of the data were set aside for the test set (holdout set), and 20% of the data
        were used for the validation set. Images were resized to 150x150 pixel squares</p>
        <p>The final model was trained for a total of 52 epochs.
        The final <b>validation set accuracy was 99.9%</b></p>
    """, unsafe_allow_html=True)

file_data = st.file_uploader("Selecciona una imagen.", type=["jpg", "jpeg", "png"])


def download_file(url):
    with st.spinner('Downloading model...'):
        # from https://stackoverflow.com/a/16696317
        local_filename = url.split('/')[-1]
        # NOTE the stream=True parameter below
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    # If you have chunk encoded response uncomment if
                    # and set chunk_size parameter to None.
                    # if chunk:
                    f.write(chunk)
        return local_filename


def fix_rotation(file_data):
    # check EXIF data to see if has rotation data from iOS. If so, fix it.
    try:
        image = Image.open(file_data)
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break

        exif = dict(image.getexif().items())

        rot = 0
        if exif[orientation] == 3:
            rot = 180
        elif exif[orientation] == 6:
            rot = 270
        elif exif[orientation] == 8:
            rot = 90

        if rot != 0:
            st.write(f"Rotating image {rot} degrees (you're probably on iOS)...")
            image = image.rotate(rot, expand=True)
            # This step is necessary because image.rotate returns a PIL.Image, not PILImage, the fastai derived class.
            image.__class__ = PILImage

    except (AttributeError, KeyError, IndexError):
        pass  # image didn't have EXIF data

    return image


# cache the model so it only gets loaded once
@st.cache(allow_output_mutation=True)
def get_model():
    if not os.path.isfile(MODEL_FILE):
        print(f"Descargando modelo desde {MODEL_URL}")
        _ = download_file(f'{MODEL_URL}')

    model = load_model(MODEL_FILE)

    print(f"Se ha cargado el modelo de la IA desde {MODEL_FILE}")

    return model


learn = get_model()

if file_data is not None:
    with st.spinner('Clasificando...'):
        # load the image from uploader; fix rotation for iOS devices if necessary
        img = fix_rotation(file_data)

        st.write('## Imagen subida')
        st.image(img, width=200)

        # Convierto a img array
        img_resized = img.resize((150,150))
        img_array = keras.preprocessing.image.img_to_array(img_resized)
        image_without_alpha = img_array[:,:,:3]
        image_without_alpha = tf.expand_dims(image_without_alpha, 0)  # Create batch axis

        # classify
        predictions = learn.predict(image_without_alpha)
        print(f"Predicciones: {predictions}")

        out_text = '<table><tr> <th>Fruta</th> <th>Confidence</th></tr>'
        etiquetas = ["Manzana","Platano","Carambola"]
        i = 0
        for p in predictions[0]:
            out_text += '<tr>' + \
                f'<td>{etiquetas[i]}</td>' + \
                f'<td>{100 * p:.02f}%</td>' + \
                        '</tr>'
            i += 1
        out_text += '</table><br><br>'
        st.markdown(out_text, unsafe_allow_html=True)
