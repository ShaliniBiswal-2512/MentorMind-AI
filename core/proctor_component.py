import os
import streamlit.components.v1 as components

proctor_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui", "proctor_component")
proctor_comp = components.declare_component("proctor_comp", path=proctor_path)
