// Copyright 2009 Peter Dolan, all rights reserved.

package net.peterd.zombierun.activity;

import com.google.android.apps.analytics.GoogleAnalyticsTracker;

import android.app.Activity;
import android.content.Context;
import android.util.Log;

public class BaseActivity extends Activity {

  @Override
  public void onStart() {
    super.onStart();
    logToAnalytics(this);
  }
  
  protected static void logToAnalytics(Context context) {
    GoogleAnalyticsTracker tracker = GoogleAnalyticsTracker.getInstance();
    tracker.start("UA-214814-13", context);
    String pageView = "/action/" + context.getClass().getSimpleName();
    Log.d("ZombieRun.BaseActivity", pageView);
    tracker.trackPageView(pageView);
    tracker.dispatch();
  }
}
