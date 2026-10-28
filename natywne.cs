// Natywne pomocniki panelu „Standardy wizualizacji” (kompilowane przez Add-Type w okno.ps1, C# 5 — .NET Framework).
using System;
using System.Drawing;
using System.Runtime.InteropServices;
using System.Windows.Forms;

namespace StandardyWizualizacji
{
    public static class Natywne
    {
        [StructLayout(LayoutKind.Sequential)]
        public struct RECT { public int Left, Top, Right, Bottom; }

        [DllImport("user32.dll")] static extern bool SetProcessDpiAwarenessContext(IntPtr wartosc);
        [DllImport("user32.dll")] public static extern uint GetDpiForWindow(IntPtr okno);
        [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr okno);
        [DllImport("user32.dll")] public static extern bool IsWindow(IntPtr okno);
        [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr okno);
        [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr okno);
        [DllImport("user32.dll")] static extern bool ReleaseCapture();
        [DllImport("user32.dll")] static extern IntPtr SendMessage(IntPtr okno, int msg, IntPtr w, IntPtr l);
        [DllImport("user32.dll", EntryPoint = "SetWindowLongPtrW")] static extern IntPtr SetWindowLongPtr(IntPtr okno, int indeks, IntPtr wartosc);
        [DllImport("user32.dll")] static extern bool GetWindowRect(IntPtr okno, out RECT r);
        [DllImport("dwmapi.dll")] static extern int DwmGetWindowAttribute(IntPtr okno, int atrybut, out RECT r, int rozmiar);

        public static void WlaczDpi()
        {
            try { SetProcessDpiAwarenessContext(new IntPtr(-4)); } catch (Exception) { }   // PER_MONITOR_AWARE_V2
        }

        public static void UstawWlasciciela(IntPtr okno, IntPtr wlasciciel)
        {
            SetWindowLongPtr(okno, -8, wlasciciel);   // GWLP_HWNDPARENT: panel nad Power BI, minimalizuje się razem z nim
        }

        public static Rectangle Prostokat(IntPtr okno)
        {
            RECT r;
            // widoczne granice (bez niewidocznej ramki zmaksymalizowanego okna)
            if (DwmGetWindowAttribute(okno, 9, out r, Marshal.SizeOf(typeof(RECT))) != 0) GetWindowRect(okno, out r);
            return Rectangle.FromLTRB(r.Left, r.Top, r.Right, r.Bottom);
        }

        public static double Skala(IntPtr okno)
        {
            try { uint d = GetDpiForWindow(okno); return d > 0 ? d / 96.0 : 1.0; } catch (Exception) { return 1.0; }
        }

        public static void Przeciagnij(IntPtr okno)
        {
            ReleaseCapture();
            SendMessage(okno, 0xA1, new IntPtr(2), IntPtr.Zero);   // WM_NCLBUTTONDOWN + HTCAPTION
        }
    }

    /// <summary>Okno bez ramki z cieniem; zmiana rozmiaru przez wąski brzeg wokół WebView2.</summary>
    public class Panel : Form
    {
        public int Brzeg = 6;
        public bool TylkoLewa = true;   // przypięty do Power BI: szerokość zmienia tylko lewa krawędź

        public Panel()
        {
            FormBorderStyle = FormBorderStyle.None;
            StartPosition = FormStartPosition.Manual;
            DoubleBuffered = true;
        }

        protected override CreateParams CreateParams
        {
            get
            {
                CreateParams cp = base.CreateParams;
                cp.ClassStyle |= 0x20000;   // CS_DROPSHADOW
                return cp;
            }
        }

        protected override void WndProc(ref Message m)
        {
            if (m.Msg == 0x84)   // WM_NCHITTEST
            {
                base.WndProc(ref m);
                long lp = m.LParam.ToInt64();
                Point p = PointToClient(new Point((short)(lp & 0xFFFF), (short)((lp >> 16) & 0xFFFF)));
                int b = Brzeg;
                bool l = p.X < b, r = p.X >= ClientSize.Width - b, t = p.Y < b, d = p.Y >= ClientSize.Height - b;
                int wynik = 0;
                if (TylkoLewa) { if (l) wynik = 10; }
                else if (t && l) wynik = 13; else if (t && r) wynik = 14; else if (d && l) wynik = 16; else if (d && r) wynik = 17;
                else if (l) wynik = 10; else if (r) wynik = 11; else if (t) wynik = 12; else if (d) wynik = 15;
                if (wynik != 0) m.Result = new IntPtr(wynik);
                return;
            }
            base.WndProc(ref m);
        }
    }
}
