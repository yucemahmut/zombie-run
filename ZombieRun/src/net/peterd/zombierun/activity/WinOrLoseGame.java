package net.peterd.zombierun.activity;

import com.google.ads.AdSenseSpec;
import com.google.ads.GoogleAdView;
import com.google.ads.AdSenseSpec.AdType;

import net.peterd.zombierun.R;
import net.peterd.zombierun.constants.ApplicationConstants;
import net.peterd.zombierun.constants.BundleConstants;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.view.KeyEvent;
import android.view.View;
import android.widget.Button;

public class WinOrLoseGame extends BaseActivity {

  private GoogleAdView adView;
  
  @Override
  protected void onCreate(Bundle savedInstanceState) {
    super.onCreate(savedInstanceState);
    
    if (getIntent().getExtras().getBoolean(BundleConstants.GAME_WON)) {
      setContentView(R.layout.win);
    } else {
      setContentView(R.layout.lose);
    }
    
    Button newGameButton = (Button) findViewById(R.id.button_new_game);
    final Intent mainMenuIntent = new Intent(this, Main.class);
    newGameButton.setOnClickListener(new View.OnClickListener() {
        public void onClick(View v) {
          startActivity(mainMenuIntent);
        }
      });
    
    // Set up GoogleAdView.
    adView = (GoogleAdView) findViewById(R.id.adview);
    new Handler().post(new Runnable() {
        public void run() {
          showAds();
        }
      });
  }
  
  @Override
  public boolean onKeyDown(int keyCode, KeyEvent event) {
    if (keyCode == KeyEvent.KEYCODE_BACK) {
      startActivity(new Intent(this, Main.class));
      return true;
    }
    return false;
  }
  
  private void showAds() {
    AdSenseSpec adSenseSpec = new AdSenseSpec(getString(R.string.adsense_pub_id))
          .setCompanyName(getString(R.string.adsense_company_name))
          .setAppName(getString(R.string.app_name))
          .setKeywords(getString(R.string.adsense_keywords))
          .setChannel(getString(R.string.adsense_channel))
          .setAdType(AdType.TEXT_IMAGE)
          .setWebEquivalentUrl(getString(R.string.about_url))
          .setAdTestEnabled(ApplicationConstants.testing());
    
    // Fetch Google ad.
    // PLEASE DO NOT CLICK ON THE AD UNLESS YOU ARE IN TEST MODE.
    // OTHERWISE, YOUR ACCOUNT MAY BE DISABLED.
    adView.showAds(adSenseSpec);
  }
}
