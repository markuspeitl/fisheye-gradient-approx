import { ChildProcessWithoutNullStreams, spawn } from "child_process";

export class PyCaller {

    private childprocess: ChildProcessWithoutNullStreams;
    private client: any = null;
    constructor() {
        console.log("PyCaller constructed");
    }

    // Spawn python subprocess and start reading from output
    public init(scriptlocation: string, callback: any): Promise<void> {
        let exectype = "python3";
        if (process.platform === "win32") {
            exectype = "python";
        }
        console.log("Spawning python process: " + scriptlocation);
        this.childprocess = spawn(exectype, [scriptlocation]);
        this.childprocess.stdin.setDefaultEncoding("utf-8");

        return this.handleScriptProcess(this.childprocess, callback);
    }

    // Sending a message to the python subprocess by writing to its stdin stream
    public sendMessage(message: string): void{
        console.log("sendMessage to PY: " + message);
        this.childprocess.stdin.cork();
        this.childprocess.stdin.write(message);
        this.childprocess.stdin.uncork();
    }

    // Send data to callback if any new data was written to the python subprocesses stdout or stderr
    private handleScriptProcess(childprocess: ChildProcessWithoutNullStreams, callback: any): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            childprocess.stderr.on("data", (data: any) => {
                return reject(data.toString("utf8"));
            });
            childprocess.stdout.on("data", (data: any) => {
                console.log("PYTHON: " + data.toString("utf8"));
                // console.log("Received data from python")
                callback(data.toString("utf8"));
            });
            /*childprocess.stdout.on("close", (code: any) => {
                // fast cast to int
                code = code | 0;
                console.log("Program closed: " + code);
                if (code === 0) {
                    console.log("python: script execution fininshed");
                    return resolve();
                } else {
                    return reject("ERROR: Program exitted with code " + code);
                }
            });*/
        });
    }

}
