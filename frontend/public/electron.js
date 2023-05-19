const {app, BrowserWindow, globalShortcut} = require('electron')
const gotTheLock = app.requestSingleInstanceLock()


function createWindow() {
    // Create the browser window.
    const win = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            webSecurity: false
        }
    })
    win.maximize()

    const url = require('url');
    const path = require('path');

    //load the index.html from a url
    //win.loadURL("http://localhost:3000/parameter")
    win.loadURL(url.format({
        pathname: path.join(__dirname, '/../build/index.html'),
        protocol: 'file:',
        slashes: true,
    }))

    // Select based on the OS
    let backend = ""
    if (process.platform === 'win32') {
        backend = path.join(process.cwd(), 'entropy_search_backend.exe')
    } else if (process.platform === 'darwin') {
        backend = path.join(process.cwd(), 'entropy_search_backend.exe')
    } else {
        backend = path.join(process.cwd(), 'entropy_search_backend.exe')
    }
    console.log("Backend: " + backend)
    var execfile = require("child_process").execFile;
    execfile(backend, {windowsHide: false,},
        (err, stdout, stderr) => {
            if (err) {
                console.log(err);
            }
            if (stdout) {
                console.log(stdout);
            }
            if (stderr) {
                console.log(stderr);
            }
        }
    )

    // Open the DevTools.
    //win.webContents.openDevTools()

    // set the Menu to null
    win.setMenu(null)
    globalShortcut.register('f5', function () {
        console.log('f5 is pressed')
        win.reload()
    })

}

let myWindow = null
if (!gotTheLock) {
    app.quit()
} else {
    app.on('second-instance', (event, commandLine, workingDirectory) => {
        // Someone tried to run a second instance, we should focus our window.
        if (myWindow) {
            if (myWindow.isMinimized()) myWindow.restore()
            myWindow.focus()
        }
    })

    ////////////////////////////////////////////////////////////////
    // Main entry point
    // Create myWindow, load the rest of the app, etc...
    app.whenReady().then(createWindow)

    // This method will be called when Electron has finished
    // initialization and is ready to create browser windows.
    // Some APIs can only be used after this event occurs.

    // Quit when all windows are closed, except on macOS. There, it's common
    // for applications and their menu bar to stay active until the user quits
    // explicitly with Cmd + Q.
    app.on('window-all-closed', () => {
        const {exec} = require("child_process");
        // Kill the backend process based on the OS
        if (process.platform === 'win32') {
            exec("taskkill /f /t /im entropy_search_backend.exe", (err, stdout, stderr) => {
                if (err) {
                    console.log(err)
                    return;
                }
                console.log(`stdout: ${stdout}`);
                console.log(`stderr: ${stderr}`);
            });
        } else {
            exec("killall entropy_search_backend.exe", (err, stdout, stderr) => {
                if (err) {
                    console.log(err)
                    return;
                }
                console.log(`stdout: ${stdout}`);
                console.log(`stderr: ${stderr}`);
            });
        }

        if (process.platform !== 'darwin') {
            app.quit()
        }
    })

    app.on('activate', () => {
        // On macOS it's common to re-create a window in the app when the
        // dock icon is clicked and there are no other windows open.

        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow()
        }
    })
}