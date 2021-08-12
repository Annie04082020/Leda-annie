import argparse
import json
import logging
import logging.handlers
import os
import sys
import typing as t

import cv2
import flask
import numpy as np

from . import leda_configuration
from . import leda_logging
from . import leda_web_service_utils
#from . import ledapk

######## Add the modules for kernel here. ##########################################################################vvvvvvvv########

from . import kernel
from .kernel import crop_label_position 
import xml.dom.minidom
#from PIL import Image, ImageDraw, ImageFont
####################################################################################################################vvvvvvvv########

class WebService(flask.Flask):
    def __init__(self, argument_parser: t.Optional[argparse.ArgumentParser] = None, configuration_file_name: t.Optional[str] = None):
        # Create web service.
        super(WebService, self).__init__(__name__, static_folder="pages/static/", template_folder="pages/templates/")
        self._inititalize_configurations(argument_parser, configuration_file_name)
        self._initialize_logger()
        self.logger.info("Configurations: %s" % self._configurations)
        self.logger.info("The web service has been created.")
        del self._configurations
        
        # Authorize by the LEDAPK.
        #if not ledapk.authorize("./leda.key", "0000000000000000000000000000000000000000000000000000000000000000"):
        #    self.logger.critical("Authorized fail.")
        #    sys.exit(1)
        #self.logger.info("Authorized succeed.")
        
        try:
            ######## Initialize the kernel here. ###################################################################vvvvvvvv########
            
            # Log hyperparameters. Remember to modify the log level to DEBUG at app.ini.
            #self.logger.debug('Initialize parameter_ka as %f.' % self._parameter_ka)
            
            pass
            
            ########################################################################################################^^^^^^^^########
        except Exception:
            self.logger.critical("An exception happened while initialing the kernel:", exc_info=True)
            sys.exit(1)
        
        ######## Implement the web services here. ##################################################################vvvvvvvv########
        
        @self.route("/", methods=["GET"])
        @self.route("/leda/sample", methods=["GET"])
        def sample():
            return flask.render_template("sample.html")
        
        @self.route("/leda/uploading", methods=["GET"])
        def uploading():
            return flask.render_template('uploading.html', allowed_image_extensions=self._allowed_image_extensions)
        
        @self.route("/leda/uploading", methods=["POST"])
        def inference():
            # Log the packet.
            self.logger.info(flask.request.values)
            
            # Authorize by the API key.
            if flask.request.values.get("api_key") != "000000000000":
                self.logger.error("Wrong api key: %s." % flask.request.values.get("api_key"))
                return flask.abort(401)
            
            # Check if file is carried by packet.
            if not flask.request.files.get("image"):
                self.logger.error("Missing image.")
                return flask.abort(400)
            
            # Read the image.
            timestamp = leda_web_service_utils.get_formatted_timestamp()
            image_bytes = flask.request.files["image"].read()
            image_np = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_UNCHANGED)
            self._log_image(image_np, timestamp)
        #TODO    
            #Run crop_label_position
            input_root_Image = flask.request.files["image"]#上傳檔案路徑
            upload_file_root_Image = input_root_Image.filename#加上附檔名
            image_file_root = os.path.join(self._temp_images_directory, upload_file_root_Image)#到temp資料夾找檔案
            self._save_image(image_np , image_file_root)#存到temp資料夾

            input_root_xml = flask.request.files["xml"]#上傳檔案路徑
            xml_file_root = os.path.join(self._temp_images_directory,"test.xml")
            input_root_xml.save(xml_file_root)
            # self._temp_images_directory.writexml(input_root_xml)
            self.logger.debug(xml_file_root)
            self.logger.debug(image_file_root)
            self.logger.debug(self._output_folder)
            # output_folder = 'download'
            crop_label_position.crop_label(xml_file_root, image_file_root, self._output_folder)
            #image_result_np=crop_label_position.bboxes['image'].copy()
            #image_result_np = bboxes['image'].copy()
            # Run the kernel scripts.
            _, returned_value = kernel.main(results = ["successfully", "called", "the", "kernel"], image = image_np)
            results = returned_value['results']
            image_result_np = returned_value['image'].copy()
            self._log_result(image_result_np, timestamp)
            
            #input image on picture
            """img = Image.open("lena.jpg")
            print(img.size)

            font = ImageFont.truetype('Pillow/Tests/fonts/FreeMono.ttf', 36)
            draw = ImageDraw.Draw(img)
            draw.text((10, 10), 'Hello', font=font, fill=(255,255,255))

            print(img.size)
            img.show()"""
            
            # Jsonify.
            return flask.jsonify("success!")
            results = json.dumps(results)
            self.logger.info("The results of \"%s\" are %s" % ("%s.%s" % (timestamp, self._log_images_extension), str(results)))
            if leda_web_service_utils.is_json_accepted(flask.request.headers):
                return flask.jsonify({"message": "200 OK", "predictions": results})
            
            # Save temp image and render the web page.
            self._remove_old_log_files(self._temp_images_directory, 0, "jpg")
            self._save_image(image_np, os.path.join(self._temp_images_directory, "%sa.jpg" % timestamp))
            #self._save_image(image_result_np, os.path.join(self._temp_images_directory, "%sb.jpg" % timestamp))
            self._save_image(image_np, os.path.join(self._temp_images_directory, "%sb.jpg" % timestamp))
            return flask.render_template('display.html', image_original_file_name="%sa.jpg" % timestamp, image_inferenced_file_name="%sb.jpg" % timestamp, image_width=800, results=str(results))
        
        ############################################################################################################^^^^^^^^########
        
        @self.errorhandler(Exception)
        def show_error_page(error):
            http_status_code = leda_web_service_utils.get_http_status_code(error)
            http_status_name = leda_web_service_utils.get_http_status_name(error)
            error_description = leda_web_service_utils.get_error_description(error)
            self.logger.error("%d %s: %s" % (http_status_code, http_status_name, error_description))
            if leda_web_service_utils.is_json_accepted(flask.request.headers):
                return flask.jsonify({"message": leda_web_service_utils.get_error_message(http_status_code, http_status_name, error_description)}), http_status_code
            return flask.render_template(leda_web_service_utils.get_error_page(http_status_code)), http_status_code
    
    def run(self) -> None:
        self.logger.info("Start the web service.")
        super(WebService, self).run(host="0.0.0.0", port=self._port)
    
    def _inititalize_configurations(self, argument_parser: t.Optional[argparse.ArgumentParser] = None, configuration_file_name: t.Optional[str] = None) -> None:
        """
        Load default settings and combine it with runtime settings. Argument will have the higher priority.
        """
        configuration_file_name = configuration_file_name or "app.ini"
        config = leda_configuration.load_configuration(filenames=configuration_file_name)
        self._configurations = leda_configuration.combine_configuration(argument_parser, config)
        for k in self._configurations:
            if type(self._configurations[k]) in [bool, int, float]:
                exec("self._%s = %s" % (k, self._configurations[k]))
            else:
                exec("self._%s = \"%s\"" % (k, self._configurations[k]))
        self._temp_images_directory = "leda/pages/static/temp/"
    
    def _initialize_logger(self) -> None:
        log_images_directory = os.path.normpath(self._log_images_directory)
        os.makedirs(log_images_directory, exist_ok=True)
        log_results_directory = os.path.normpath(self._log_results_directory)
        os.makedirs(log_results_directory, exist_ok=True)
        
        handlers = []
        if self._log_stream:
            handlers.append(leda_logging.get_stream_handler())
        handlers.append(leda_logging.get_rotating_file_handler(self._log_files_name, self._log_files_count))
        
        loggers = dict()
        loggers[__name__] = leda_logging.get_logger(__name__, self._log_level, handlers = handlers)
        loggers["werkzeug"] = leda_logging.get_logger("werkzeug", self._log_level, handlers = handlers)
        
        self.logger.info("Log will be saved in \"%s\"" % os.path.normpath(os.path.join(self._log_files_name, "..")))
        self.logger.info("Log image will be saved in \"%s\"" % log_images_directory)
        del self._log_level
        del self._log_stream
        del self._log_files_name
        del self._log_files_count
    
    def _log_image(self, image_np: str, timestamp: str):
        self._remove_old_log_files(self._log_images_directory, self._log_images_count - 1, self._log_images_extension)
        self._save_image(image_np, os.path.join(self._log_images_directory, "%s.%s" % (timestamp, self._log_images_extension)))
    
    def _log_result(self, image_result_np: str, timestamp: str):
        self._remove_old_log_files(self._log_results_directory, self._log_results_count - 1, "jpg")
        self._save_image(image_result_np, os.path.join(self._log_results_directory, "%s.jpg" % timestamp))
    
    def _remove_old_log_files(self, directory: str, log_files_count: t.Optional[int] = -1, extension: t.Optional[str] = None) -> None:
        if log_files_count < 0:
            return
        extension = extension or "jpg"
        files = [f for f in os.listdir(directory) if (len(f) > 1 + len(extension) and f[-(1+len(extension)):] == '.%s' % extension)]
        if len(files) <= log_files_count:
            return
        files = sorted(files)
        for f in files[:(len(files)-log_files_count)]:
            file_name = os.path.join(directory, f)
            os.remove(file_name)
            self.logger.info("Delete old log file: \"%s\"." % file_name)
    
    def _save_image(self, image_np: np.ndarray, file_name: str) -> None:
        cv2.imwrite(file_name, image_np)
        self.logger.info('Image file saved: "%s".' % file_name)

