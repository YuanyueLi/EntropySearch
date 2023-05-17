const { app, BrowserWindow, globalShortcut } = require('electron')
const url = require('url');
const path = require('path');


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

    //load the index.html from a url
    //win.loadURL("http://localhost:3000/parameter")
    win.loadURL(url.format({
        pathname: path.join(__dirname, '/../build/index.html'),
        protocol: 'file:',
        slashes: true,
    }))


    // Open the DevTools.
    //win.webContents.openDevTools()

    // set the Menu to null
    win.setMenu(null)
    globalShortcut.register('f5', function () {
        console.log('f5 is pressed')
        win.reload()
    })

}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', () => {
    const { exec } = require("child_process");
    // Kill the backend process based on the OS
    if (process.platform == 'win32') {
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

// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and require them here.


app.whenReady().then(() => {
    // Select based on the OS
    const backend = path.join(process.cwd(), 'entropy_search_backend.exe')
    console.log("Backend: " + backend)
    var execfile = require("child_process").execFile;
    execfile(backend, { windowsHide: false, },
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
}).then(createWindow)