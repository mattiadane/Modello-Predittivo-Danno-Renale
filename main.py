
import subprocess

class Application :

    def start_backend(self):
        pass

    def start_frontend(self):
        subprocess.run(["streamlit", "run", "front-end/home_page.py"])

    def run(self):
        self.start_frontend()




if __name__ == "__main__":
    app = Application()
    app.run()