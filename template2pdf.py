import os
import sys
import json
import base64
from contextlib import suppress
from jinja2 import FileSystemLoader, Environment
from selenium.webdriver import Chrome, ChromeOptions as Options


class Template2PDF:
    """
    Renders and converts a Jinja2 template into a PDF file.
    
    CSS styles in a ´.css´ file are not supported.
    The style must be a remote URL on a ´link´ tag or a style in a ´style´ tag.

    Chromium/Chrome and chromedriver must be installed and added to PATH.
    """

    def __init__(self, template: str):
        r = template.split("/")
        template_name = r[-1]
        path = "/".join(r[0:-1])
        del r

        self.__template = Environment(
            loader=FileSystemLoader(searchpath=path if path else "./")
        ).get_template(template_name)

        self.text = None

    def render(self, data: dict):
        self.text = self.__template.render(**data)
        return self

    def write_pdf(self, target=None, options={}):
        """
        Writes to file. If no ´target´ is given a base64 string is returned.
        """
        try:
            if not self.text:
                raise RuntimeError("The template must be rendered first.")

            driver_options = Options()
            driver_options.headless = True
            driver = Chrome(options=driver_options)

            with open("page.html", "w+t") as fp:
                fp.write(self.text)

            file_path = os.getcwd() + "/page.html"
            driver.get("file:///" + file_path)

            print_options = {
                "landscape": False,
                "displayHeaderFooter": False,
                "printBackground": True,
                "preferCSSPageSize": True,
                **options,
            }

            result = self.__send_devtools(driver, "Page.printToPDF", print_options)

            if target:
                with open(target, "w+b") as fp:
                    fp.write(base64.b64decode(result["data"]))
                return
            else:
                return result["data"]
        except Exception as e:
            raise e
        finally:
            driver.quit()
            with suppress(OSError):
                os.remove(file_path)

    def __send_devtools(self, driver, cmd, params={}):
        resource = (
            "/session/%s/chromium/send_command_and_get_result" % driver.session_id
        )
        url = driver.command_executor._url + resource
        body = json.dumps({"cmd": cmd, "params": params})
        response = driver.command_executor._request("POST", url, body)

        if response.get("status", False):
            raise Exception(response.get("value"))
        return response.get("value")


if __name__ == "__main__":
    program, template, input_, output = sys.argv[0:]
    del program

    with open(input_, "r") as fp:
        data = json.load(fp)

    Template2PDF(template).render(data).write_pdf(output)
