package net.peterd.zombierun.activity;

import net.peterd.zombierun.R;
import android.app.Activity;
import android.os.Bundle;
import android.view.Window;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;

public class WebGame extends Activity {

  @Override
  protected void onCreate(Bundle savedInstanceState) {
    super.onCreate(savedInstanceState);

    getWindow().requestFeature(Window.FEATURE_PROGRESS);

    WebView webview = new WebView(this);
    setContentView(webview);

    WebSettings settings = webview.getSettings();
    settings.setJavaScriptEnabled(true);
    settings.setBuiltInZoomControls(false);
    settings.setSupportZoom(false);
    settings.setUserAgentString(getString(R.string.webgame_useragent));

    final Activity activity = this;
    webview.setWebChromeClient(new WebChromeClient() {
      @Override
      public void onProgressChanged(WebView view, int progress) {
        // Activities and WebViews measure progress with different scales.
        // The progress meter will automatically disappear when we reach 100%
        activity.setProgress(progress * 1000);
      }
    });

    webview.loadUrl(getString(R.string.web_game_url));
  }
}
