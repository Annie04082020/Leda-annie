import argparse

import leda

if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(prog="LEDA-AI-web-service", description="The web service for LEDA AI model.")
    argument_parser.add_argument("--port", type=int, help="port number")
    
    web_service = leda.WebService(argument_parser)
    web_service.run()

