// Copyright 2009 Peter Dolan, all rights reserved.

package net.peterd.zombierun.activity;

import com.google.android.apps.analytics.GoogleAnalyticsTracker;

import android.app.Activity;
import android.util.Log;

public class BaseActivity extends Activity {

  protected GoogleAnalyticsTracker tracker;
  
  @Override
  public void onStart() {
    super.onStart();
    tracker = GoogleAnalyticsTracker.getInstance();
    tracker.start("UA-214814-13", this);
    String pageView = "/action/" + this.getClass().getSimpleName();
    Log.d("ZombieRun.BaseActivity", pageView);
    tracker.trackPageView(pageView);
  }
}
