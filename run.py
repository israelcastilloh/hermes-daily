import app.decorators.auxiliary as auxiliary
from pyngrok import ngrok, conf
from app import create_app
import logging

#---------------------------------------------
# CREATE APP
#---------------------------------------------
app = create_app()

if __name__ == "__main__":        
    #---------------------------------------------
    # CREATE NGROK CONFIG FILE
    #---------------------------------------------
    
    # Create YAML file for Ngrok 
    auxiliary.create_config_yaml()

    # Open a HTTP tunnel on the default port 8000
    conf.get_default().config_path = "./data/ngrok_config.yml"

    # Establecer el túnel HTTP con las opciones especificadas
    http_tunnel = ngrok.connect(name="similin_tunnel")

    try: 
        #---------------------------------------------
        # Block until CTRL-C or some other terminating event
        #---------------------------------------------
        ngrok_process = ngrok.get_ngrok_process()

        # Delete YAML file for security
        auxiliary.delete_config_yaml()

        #---------------------------------------------
        # RUN APP
        #---------------------------------------------
        logging.info("Hermes Daily App Starting")
        app.run(host="127.0.0.1", port=8000)

        ngrok_process.proc.wait()

    except KeyboardInterrupt:
        logging.info("Shutting down server.")
        ngrok.kill()
        
