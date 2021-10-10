import webview


def open_file_dialog(window):
    file_types = ('Image Files (*.bmp;*.jpg;*.gif)', 'All files (*.*)')
    result = window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=True, file_types=file_types)
    print(result)


class Api:
    def select_file_for_spectral_file(self):
        file_types = ('Spectral files (*.msp;*.mgf;*.mzML)')
        filename = window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
        if not filename:
            return ""
        return filename

    def select_file_for_spectral_library(self):
        file_types = ('MSP files (*.msp)')
        filename = window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
        if not filename:
            return ""
        return filename

    def save_file_path(self):
        filename = webview.windows[0].create_file_dialog(webview.SAVE_DIALOG)
        if not filename:
            return ""
        return filename


if __name__ == '__main__':
    window = webview.create_window('Entropy search', '../frontend/build/index.html', js_api=Api(),
                                   width=800, height=610)
    webview.start()
