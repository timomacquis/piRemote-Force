using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.IO;
using System.Linq;
using System.Net;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;
[assembly:System.Runtime.Versioning.TargetFramework(".NETFramework,Version=v4.8",FrameworkDisplayName=".NET Framework 4.8")]
[assembly:System.Reflection.AssemblyTitle("πRemote")]
[assembly:System.Reflection.AssemblyProduct("πRemote")]
[assembly:System.Reflection.AssemblyVersion("0.1.0.0")]
[assembly:System.Reflection.AssemblyFileVersion("0.1.0.0")]

sealed class PiButton : Control {
    public bool Lit;
    public Color Accent = Color.FromArgb(215,190,125);
    public PiButton() {SetStyle(ControlStyles.UserPaint|ControlStyles.AllPaintingInWmPaint|ControlStyles.OptimizedDoubleBuffer|ControlStyles.ResizeRedraw|ControlStyles.Selectable|ControlStyles.StandardClick,true);Font=new Font("Segoe UI",8.5f);Cursor=Cursors.Hand;TabStop=true;AccessibleRole=AccessibleRole.PushButton;}
    protected override void OnMouseDown(MouseEventArgs e){if(e.Button==MouseButtons.Left)Focus();base.OnMouseDown(e);Invalidate();}
    protected override void OnGotFocus(EventArgs e){base.OnGotFocus(e);Invalidate();}
    protected override void OnLostFocus(EventArgs e){base.OnLostFocus(e);Invalidate();}
    protected override void OnKeyDown(KeyEventArgs e){if(Enabled&&(e.KeyCode==Keys.Space||e.KeyCode==Keys.Enter)){e.Handled=true;e.SuppressKeyPress=true;OnClick(EventArgs.Empty);}else base.OnKeyDown(e);}
    protected override void OnEnabledChanged(EventArgs e){base.OnEnabledChanged(e);Invalidate();}
    protected override void OnPaintBackground(PaintEventArgs e){e.Graphics.Clear(Parent==null?Color.FromArgb(23,28,31):Parent.BackColor);}
    protected override void OnPaint(PaintEventArgs e) {
        e.Graphics.SmoothingMode=SmoothingMode.AntiAlias;
        e.Graphics.Clear(Parent==null?Color.FromArgb(23,28,31):Parent.BackColor);
        RectangleF r=new RectangleF(0.5f,0.5f,Width-1,Height-1);
        using(GraphicsPath path=new GraphicsPath()) {
            float d=Math.Min(12f*e.Graphics.DpiX/96f,r.Height-1);path.AddArc(r.Left,r.Top,d,d,180,90);path.AddArc(r.Right-d,r.Top,d,d,270,90);path.AddArc(r.Right-d,r.Bottom-d,d,d,0,90);path.AddArc(r.Left,r.Bottom-d,d,d,90,90);path.CloseFigure();
            Color fill=Lit?Color.FromArgb((int)(Accent.R*.19+23*.81),(int)(Accent.G*.19+28*.81),(int)(Accent.B*.19+31*.81)):Color.FromArgb(35,43,48);
            using(Brush b=new SolidBrush(fill))e.Graphics.FillPath(b,path);
            using(Pen p=new Pen(Lit?Accent:Focused?Color.FromArgb(155,160,165):Color.FromArgb(79,91,99),1f))e.Graphics.DrawPath(p,path);
        }
        Color color=!Enabled?Color.FromArgb(105,112,116):Lit?Accent:ForeColor;
        TextRenderer.DrawText(e.Graphics,Text,Font,ClientRectangle,color,TextFormatFlags.HorizontalCenter|TextFormatFlags.VerticalCenter|TextFormatFlags.SingleLine|TextFormatFlags.NoPadding);
    }
}

sealed class PiRemote : Form {
    readonly Color ink=Color.FromArgb(233,231,215);
    readonly Color violet=Color.FromArgb(192,157,219);
    readonly Label state=new Label(),hint=new Label();
    readonly List<PiButton> buttons=new List<PiButton>();
    readonly PiButton[] tracks=new PiButton[8];
    readonly ToolTip tips=new ToolTip();
    readonly CancellationTokenSource closing=new CancellationTokenSource();
    readonly SemaphoreSlim sendLock=new SemaphoreSlim(1,1);
    readonly JavaScriptSerializer json=new JavaScriptSerializer(){MaxJsonLength=16*1024*1024};
    readonly TextBox hostBox=new TextBox();
    PiButton connectButton,bankOne,bankTwo;
    CancellationTokenSource session;
    Task sessionTask;
    bool activationOffered,allowActivation=true,activating;
    string fixtureEndpoint;
    PiButton shiftButton,editButton,pluginButton,previousButton,nextButton,playButton,recordButton;
    bool ready,busy,shift,edit,preview,wanted,disconnecting,allowClose;
    int slot=-1,bank;
    public PiRemote(bool previewMode) {
        SuspendLayout();preview=previewMode;Text="πRemote";ClientSize=new Size(288,476);BackColor=Color.FromArgb(23,28,31);ForeColor=ink;
        FormBorderStyle=FormBorderStyle.FixedToolWindow;ShowInTaskbar=true;MaximizeBox=false;StartPosition=FormStartPosition.Manual;
        string iconPath=Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"piRemote.ico");if(File.Exists(iconPath))Icon=new Icon(iconPath);
        AutoScaleDimensions=new SizeF(96,96);AutoScaleMode=AutoScaleMode.Dpi;Font=new Font("Segoe UI",8.5f);
        state.Text="Disconnected";
        CheckBox pin=new CheckBox(){Text="Pin",AutoSize=true,ForeColor=ink};pin.SetBounds(232,430,46,20);pin.CheckedChanged+=delegate{TopMost=pin.Checked;};Controls.Add(pin);
        hostBox.SetBounds(10,14,160,25);hostBox.Font=new Font("Segoe UI",10f);hostBox.BackColor=Color.FromArgb(35,43,48);hostBox.ForeColor=ink;hostBox.BorderStyle=BorderStyle.FixedSingle;tips.SetToolTip(hostBox,"Force IP address · saved when connecting");
        string ipFile=Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"Force-IP.txt");hostBox.Text=File.Exists(ipFile)?File.ReadAllText(ipFile).Trim():"";Controls.Add(hostBox);
        connectButton=new PiButton(){Text="CONNECT",ForeColor=ink,Font=new Font("Segoe UI",7.5f),Accent=Color.FromArgb(113,190,145)};connectButton.SetBounds(176,18,102,16);connectButton.Click+=async delegate{if(wanted)await Disconnect();else await BeginConnect();};Controls.Add(connectButton);
        string[] transport={"▶ PLAY","■ STOP","● REC","CONTINUE"};string[] commands={"play","stop","record","continue"};
        for(int i=0;i<4;i++){string cmd=commands[i];PiButton b=Add(transport[i],10+i*68,68,64,async delegate{await Transport(cmd);});if(i==0){playButton=b;b.Accent=Color.FromArgb(113,190,145);}if(i==2){recordButton=b;b.Accent=Color.FromArgb(222,112,130);}}
        tips.SetToolTip(playButton,"Green follows PLAY/STOP button events. This is not audio-engine telemetry.");
        tips.SetToolTip(recordButton,"Red follows the Force REC button (record arm). Press PLAY to start if stopped.");
        string[] views={"MATRIX","MIXER","CLIP","STEP SEQ","MENU","NAVIGATE"};int[] notes={3,11,9,117,2,0};
        for(int i=0;i<6;i++){int note=notes[i];Add(views[i],10+(i%4)*68,i<4?112:156,64,async delegate{await Press(note,false);});}
        shiftButton=Add("SHIFT",146,156,64,delegate{shift=!shift;RefreshButtons();});
        editButton=Add("EDIT",214,156,64,delegate{edit=!edit;RefreshButtons();});
        pluginButton=Add("EDIT PLUGIN",78,340,132,async delegate{if(slot>=0)await Choose(slot,true);});
        tips.SetToolTip(shiftButton,"SHIFT applies to the next press, then releases.");tips.SetToolTip(editButton,"EDIT + a track opens its editor.");
        bankOne=Add("TRACKS 01 – 08",10,204,131,async delegate{await SwitchBank(0);});bankTwo=Add("TRACKS 09 – 16",147,204,131,async delegate{await SwitchBank(1);});
        tips.SetToolTip(bankOne,"Opens Matrix and shifts the bank of eight tracks. Verify the visible bank after navigating on the Force.");tips.SetToolTip(bankTwo,tips.GetToolTip(bankOne));
        for(int i=0;i<8;i++){int n=i;tracks[i]=Add((i+1).ToString("00"),10+(i%4)*68,248+(i/4)*44,64,async delegate{await Choose(n,false);});}
        previousButton=Add("◀ TRACK",10,340,64,async delegate{if(slot>0)await Choose(slot-1,false);else if(slot==0&&bank==1){await SwitchBank(0);if(bank==0)await Choose(7,false);}});
        nextButton=Add("TRACK ▶",214,340,64,async delegate{if(slot>=0&&slot<7)await Choose(slot+1,false);else if(slot==7&&bank==0){await SwitchBank(1);if(bank==1)await Choose(0,false);}});
        string[] arrows={"↑","↓","←","→"};for(int i=0;i<4;i++){int note=112+i;Add(arrows[i],10+i*68,384,64,async delegate{await Press(note,false);});}
        hint.SetBounds(10,430,206,38);hint.Font=new Font("Segoe UI",8f);hint.ForeColor=Color.FromArgb(167,173,179);hint.Text="Enter the Force IP, then Connect.";Controls.Add(hint);
        tips.SetToolTip(previousButton,"Follows the last track selected here. After selecting on the Force, select its number here again.");tips.SetToolTip(nextButton,tips.GetToolTip(previousButton));
        RefreshButtons();
        ResumeLayout(false);
        Shown+=delegate{Rectangle work=Screen.FromControl(this).WorkingArea;Location=new Point(work.Left+8,work.Top+8);};
        FormClosing+=async delegate(object sender,FormClosingEventArgs e){if(preview||allowClose)return;e.Cancel=true;if(disconnecting||activating)return;await Disconnect();allowClose=true;Close();};
        FormClosed+=delegate{closing.Cancel();tips.Dispose();};
    }
    PiButton Add(string text,int x,int y,int width,EventHandler handler) {
        PiButton b=new PiButton(){Text=text,ForeColor=ink};b.SetBounds(x,y,width,36);b.Click+=handler;buttons.Add(b);Controls.Add(b);return b;
    }
    void RefreshButtons() {
        if(IsDisposed)return;
        hostBox.Enabled=!wanted&&!disconnecting;connectButton.Enabled=!disconnecting&&!activating;connectButton.Text=wanted?(ready?"DISCONNECT":"CANCEL"):"CONNECT";
        connectButton.Lit=ready;connectButton.Invalidate();
        foreach(PiButton b in buttons)b.Enabled=ready&&!busy;
        previousButton.Enabled=ready&&!busy&&slot>=0&&(slot>0||bank>0);nextButton.Enabled=ready&&!busy&&slot>=0&&(slot<7||bank<1);pluginButton.Enabled=ready&&!busy&&slot>=0;
        shiftButton.Lit=shift;editButton.Lit=edit;
        bankOne.Lit=bank==0;bankTwo.Lit=bank==1;
        for(int i=0;i<8;i++){tracks[i].Lit=i==slot;tracks[i].Accent=violet;tracks[i].Text=(bank*8+i+1).ToString("00");}
        foreach(PiButton b in buttons)b.Invalidate();
    }
    public static string Surface(IEnumerable<int> notes,int velocity) {
        List<int> bytes=new List<int>();foreach(int n in notes){bytes.Add(144);bytes.Add(n);bytes.Add(velocity);}
        return "{\"t\":\"surface\",\"bytes\":["+string.Join(",",bytes)+"]}";
    }
    async Task Send(string data) {
        CancellationToken token=session==null?closing.Token:session.Token;
        await sendLock.WaitAsync(token);
        try {if(!ready)throw new IOException("Connection interrupted");string reply=await Request("/command",data,token);var result=json.DeserializeObject(reply) as Dictionary<string,object>;if(result==null||!result.ContainsKey("ok")||!Convert.ToBoolean(result["ok"]))throw new IOException("Command rejected");}
        finally{sendLock.Release();}
    }
    async Task<string> Request(string path,string body,CancellationToken token){
        HttpWebRequest request=(HttpWebRequest)WebRequest.Create((fixtureEndpoint??"http://127.0.0.1:16732")+path);
        request.Proxy=null;request.KeepAlive=false;request.ServicePoint.Expect100Continue=false;request.Timeout=3000;request.ReadWriteTimeout=3000;
        using(token.Register(delegate{request.Abort();})){
            try{
                if(body!=null){request.Method="POST";request.ContentType="application/json";byte[] b=Encoding.UTF8.GetBytes(body);request.ContentLength=b.Length;using(Stream output=await request.GetRequestStreamAsync()){await output.WriteAsync(b,0,b.Length,token);}}
                using(WebResponse response=await request.GetResponseAsync())using(StreamReader input=new StreamReader(response.GetResponseStream()))return await input.ReadToEndAsync();
            }catch(WebException){token.ThrowIfCancellationRequested();throw;}
        }
    }
    async Task Transport(string cmd) {
        try{await Send("{\"t\":\"transport\",\"cmd\":\""+cmd+"\"}");TransportColor(cmd);hint.Text="Command sent: "+cmd.ToUpperInvariant();}
        catch(Exception e){if(!IsDisposed)hint.Text=e.Message;}
    }
    void TransportColor(string cmd){if(cmd=="play"||cmd=="continue")playButton.Lit=true;if(cmd=="record")recordButton.Lit=!recordButton.Lit;if(cmd=="stop"){playButton.Lit=false;recordButton.Lit=false;}playButton.Invalidate();recordButton.Invalidate();}
    async Task<bool> Press(int note,bool forceEdit) {
        if(!ready||busy)return false;busy=true;RefreshButtons();List<int> held=new List<int>();bool success=false;
        try {
            List<int> mods=new List<int>();if(shift)mods.Add(49);if(edit||forceEdit)mods.Add(37);
            if(mods.Count>0){await Send(Surface(mods,127));held.AddRange(mods);await Task.Delay(70,closing.Token);}
            await Send(Surface(new[]{note},127));held.Add(note);await Task.Delay(120,closing.Token);hint.Text="Command sent to Force";success=true;
        }catch(Exception e){if(!IsDisposed)hint.Text=e.Message;}
        {
            held.Reverse();if(held.Count>0&&ready&&!closing.IsCancellationRequested){try{await Send(Surface(held,0));}catch{}}
            shift=edit=false;busy=false;RefreshButtons();
        }
        return success;
    }
    async Task Choose(int n,bool forceEdit) {if(await Press(96+n,forceEdit)){slot=n;hint.Text="Track selected here: "+(bank*8+n+1).ToString("00")+" · check Force bank";RefreshButtons();}}
    async Task SwitchBank(int target) {
        if(target==bank||!ready||busy)return;
        shift=edit=false;
        if(!await Press(3,false))return;
        shift=true;if(!await Press(target>bank?115:114,false))return;
        bank=target;slot=-1;hint.Text="Bank "+(bank==0?"01–08":"09–16")+" requested · check on Force";RefreshButtons();
    }
    static string Tunnel(string command,string host) {
        string helper=Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"connect.py");if(!File.Exists(helper))throw new IOException("connect.py is missing.");
        string drive=Path.GetPathRoot(helper).Substring(0,1).ToLowerInvariant();string linux="/mnt/"+drive+helper.Substring(2).Replace('\\','/');
        ProcessStartInfo info=new ProcessStartInfo("wsl.exe","-d Ubuntu -- python3 \""+linux+"\" "+command+(host==null?"":" "+host)){UseShellExecute=false,CreateNoWindow=true,RedirectStandardOutput=true,RedirectStandardError=true};
        using(Process p=Process.Start(info)){Task<string> output=p.StandardOutput.ReadToEndAsync(),error=p.StandardError.ReadToEndAsync();if(!p.WaitForExit(40000)){p.Kill();throw new IOException("Connection timed out.");}Task.WaitAll(output,error);if(p.ExitCode!=0)throw new IOException(error.Result.Trim());return output.Result;}
    }
    static void ActivateForce(string host){
        string script=Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"Activate-Force.ps1");
        if(!File.Exists(script))throw new IOException("Activate-Force.ps1 is missing.");
        ProcessStartInfo info=new ProcessStartInfo("powershell.exe","-NoProfile -File \""+script+"\" -ForceIP "+host+" -ProjectSaved"){UseShellExecute=false,CreateNoWindow=true,RedirectStandardOutput=true,RedirectStandardError=true};
        using(Process p=Process.Start(info)){Task<string> output=p.StandardOutput.ReadToEndAsync(),error=p.StandardError.ReadToEndAsync();if(!p.WaitForExit(120000)){p.Kill();throw new IOException("Activation timed out. Check the Force before retrying.");}Task.WaitAll(output,error);if(p.ExitCode!=0)throw new IOException(error.Result.Trim()+" "+output.Result.Trim());}
    }
    async Task BeginConnect() {
        if(wanted||disconnecting)return;
        string host=hostBox.Text.Trim();System.Net.IPAddress ip;
        if(!System.Net.IPAddress.TryParse(host,out ip)||ip.AddressFamily!=System.Net.Sockets.AddressFamily.InterNetwork){hint.Text="Invalid IPv4 address.";return;}
        try{File.WriteAllText(Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"Force-IP.txt"),host,new UTF8Encoding(false));}catch(Exception e){hint.Text=e.Message;return;}
        wanted=true;activationOffered=false;session=CancellationTokenSource.CreateLinkedTokenSource(closing.Token);RefreshButtons();sessionTask=ConnectLoop(host,session.Token);await Task.Yield();
    }
    async Task Disconnect() {
        if(disconnecting||activating)return;disconnecting=true;wanted=false;RefreshButtons();state.Text="Disconnecting…";
        if(ready){try{await Send("{\"t\":\"release\"}");}catch{}}ready=false;
        if(session!=null)session.Cancel();
        if(sessionTask!=null){try{await sessionTask;}catch{}}
        try{if(fixtureEndpoint==null)await Task.Run(()=>Tunnel("disconnect",null));}catch(Exception e){tips.SetToolTip(connectButton,e.Message);}
        if(session!=null){session.Dispose();session=null;}sessionTask=null;busy=shift=edit=false;playButton.Lit=recordButton.Lit=false;slot=-1;disconnecting=false;state.Text="● Disconnected";hint.Text="IP saved · disconnected.";RefreshButtons();
    }
    async Task ConnectLoop(string host,CancellationToken token) {
        state.Text="Connecting to Force…";
        while(!token.IsCancellationRequested) {
            Exception failure=null;
            try {
                if(fixtureEndpoint==null)await Task.Run(()=>Tunnel("connect",host));token.ThrowIfCancellationRequested();
                Receive(await Request("/info",null,token));
                while(!token.IsCancellationRequested) {
                    Receive(await Request("/state",null,token));await Task.Delay(750,token);
                }
            }catch(OperationCanceledException){break;}catch(Exception e){failure=e;if(!IsDisposed){state.Text="Connection lost";hint.Text=e.Message.Contains("PIREMOTE_NOT_INSTALLED")?"Install the Force addin ZIP first.":"Retrying in 4 seconds…";tips.SetToolTip(connectButton,e.Message);}}
            finally{ready=false;slot=-1;shift=edit=false;RefreshButtons();}
            if(failure!=null&&failure.Message.Contains("ACTIVATION_REQUIRED")&&allowActivation&&!activationOffered&&!token.IsCancellationRequested){
                activationOffered=true;
                DialogResult answer=MessageBox.Show(this,"πRemote is installed on the Force but is not active.\n\nActivate it and restart MPC now?\nSave your project first: unsaved changes will be lost.","πRemote · Activate Force addin",MessageBoxButtons.YesNo,MessageBoxIcon.Question,MessageBoxDefaultButton.Button2);
                if(answer==DialogResult.Yes){
                    activating=true;RefreshButtons();hint.Text="Activating addin · restarting MPC…";Exception error=null;
                    try{await Task.Run(()=>ActivateForce(host));}catch(Exception e){error=e;}
                    activating=false;RefreshButtons();
                    if(error==null)continue;hint.Text="Activation failed · hover CONNECT for details";tips.SetToolTip(connectButton,error.Message);
                }
            }
            try{await Task.Delay(4000,token);}catch(OperationCanceledException){break;}
        }
    }
    void Receive(string raw) {
        Dictionary<string,object> m=json.DeserializeObject(raw) as Dictionary<string,object>;if(m==null||!m.ContainsKey("t"))return;
        string type=Convert.ToString(m["t"]);
        if(type=="hello") {
            if(!m.ContainsKey("product")||Convert.ToString(m["product"])!="piremote")throw new IOException("This is not a πRemote addin.");
            if(!m.ContainsKey("protocol")||Convert.ToInt32(m["protocol"])!=1)throw new IOException("Unsupported πRemote protocol.");
            if(!m.ContainsKey("ready")||!Convert.ToBoolean(m["ready"]))throw new IOException("The Force control surface is not ready yet.");
            ready=true;state.Text="● Connected";hint.Text="Select a track · EDIT opens its plugin";RefreshButtons();
        }
        if(type=="error")hint.Text=m.ContainsKey("msg")?Convert.ToString(m["msg"]):"Command rejected";
        if(type=="transport") {
            bool playing=m.ContainsKey("playing")&&Convert.ToBoolean(m["playing"]),recording=m.ContainsKey("recording")&&Convert.ToBoolean(m["recording"]);
            if(m.ContainsKey("source")&&Convert.ToString(m["source"])!=""){playButton.Lit=playing;recordButton.Lit=recording;playButton.Invalidate();recordButton.Invalidate();}
            if(m.ContainsKey("source")&&Convert.ToString(m["source"])!="")state.Text=recording?"● FORCE · recording":playing?"● FORCE · playing":"● FORCE · stopped";
        }
    }
    public void Preview(string path) {hostBox.Text="192.0.2.70";ready=wanted=true;slot=1;shift=true;playButton.Lit=recordButton.Lit=true;state.Text="● Connected";hint.Text="Track selected here: 02 · bank 01–08";RefreshButtons();Show();Application.DoEvents();using(Bitmap image=new Bitmap(Width,Height)){DrawToBitmap(image,new Rectangle(0,0,Width,Height));image.Save(path);}Close();}
    public void CheckLayout() {
        foreach(PiButton b in buttons){if(b.Height!=buttons[0].Height||b.Left<0||b.Top<0||b.Right>ClientSize.Width||b.Bottom>ClientSize.Height)throw new Exception("Invalid layout "+b.Text);}
        if(Math.Abs(connectButton.Height*9-buttons[0].Height*4)>9)throw new Exception("Invalid connection button height");
        if(Surface(new[]{37,96},0)!="{\"t\":\"surface\",\"bytes\":[144,37,0,144,96,0]}")throw new Exception("Invalid protocol");
        if(typeof(PiButton).BaseType!=typeof(Control))throw new Exception("Native button renderer still present");
        TransportColor("play");if(!playButton.Lit)throw new Exception("PLAY indicator");
        TransportColor("record");if(!recordButton.Lit||!playButton.Lit)throw new Exception("REC indicator");
        Receive("{\"t\":\"transport\",\"playing\":false,\"recording\":false,\"source\":\"\"}");if(!recordButton.Lit)throw new Exception("Empty state should not clear indicators");
        Receive("{\"t\":\"transport\",\"playing\":false,\"recording\":false,\"source\":\"mmc\"}");if(recordButton.Lit||playButton.Lit)throw new Exception("Live state override");
        TransportColor("continue");TransportColor("stop");if(recordButton.Lit||playButton.Lit)throw new Exception("STOP indicator");
    }
    public void ConnectionTest(string path,string endpoint) {
        allowActivation=false;
        if(endpoint!=null){Uri uri=new Uri(endpoint);if(uri.Scheme!="http"||!uri.IsLoopback)throw new Exception("Test endpoint must be local HTTP");fixtureEndpoint=endpoint.TrimEnd('/');hostBox.Text="127.0.0.1";}
        Shown+=async delegate{
            await BeginConnect();for(int i=0;i<200&&!ready;i++)await Task.Delay(100);
            bool connected=ready;await Disconnect();bool disconnected=!ready&&!wanted&&session==null;
            await BeginConnect();for(int i=0;i<200&&!ready;i++)await Task.Delay(100);
            bool reconnected=ready;await Disconnect();
            File.WriteAllText(path,"{\"connected\":"+(connected?"true":"false")+",\"disconnected\":"+(disconnected?"true":"false")+",\"reconnected\":"+(reconnected?"true":"false")+",\"transport_or_navigation_commands_sent\":0}");allowClose=true;Close();
        };
    }
}
static class Program {
    [DllImport("user32.dll",CharSet=CharSet.Unicode)]static extern IntPtr FindWindow(string cls,string title);
    [DllImport("user32.dll")]static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")]static extern bool ShowWindow(IntPtr h,int n);
    [STAThread]static int Main(string[] args) {
        Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);
        if(args.Length>0&&args[0]=="--selftest"){using(PiRemote f=new PiRemote(true)){f.CheckLayout();}return 0;}
        if(args.Length==2&&args[0]=="--preview"){using(PiRemote f=new PiRemote(true)){f.CheckLayout();f.Preview(args[1]);}return 0;}
        if((args.Length==2||args.Length==3)&&args[0]=="--connection-test"){using(PiRemote f=new PiRemote(false)){f.ConnectionTest(args[1],args.Length==3?args[2]:null);Application.Run(f);}return 0;}
        bool created;using(Mutex one=new Mutex(true,"Local\\PiRemoteStandalone",out created)){if(!created){IntPtr h=FindWindow(null,"πRemote");if(h!=IntPtr.Zero){ShowWindow(h,9);SetForegroundWindow(h);}return 0;}Application.Run(new PiRemote(false));}return 0;
    }
}
