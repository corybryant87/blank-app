import streamlit as st

# Streamlit app that asks for name and says hello

def main():
    st.title('Hello App')
    
    name = st.text_input('Please enter your name:')
    
    if name:
        st.write('Hello, ' + name + '!')
        st.success('Welcome, ' + name + '!')

if __name__ == '__main__':
    main()

print('Streamlit app executed successfully')