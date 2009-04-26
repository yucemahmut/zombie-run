package net.peterd.zombierun.io;

import java.io.BufferedReader;
import java.io.IOException;
import java.net.MalformedURLException;
import java.util.HashMap;
import java.util.Map;

import net.peterd.zombierun.util.Log;

/**
 * Reads updates formatted as:
 * 
 * APPLICATION_ID:<android market application id>
 * VERSION:<newest android market application version>
 * 
 * TODO: Write tests!
 *
 * @author Peter Dolan (peterjdolan@gmail.com)
 */
public class UpdateChecker {
  private static final String TAG = "ZombieRun.UpdateChecker";
  private static final String delimiter = ":";

  public enum FIELD {
    APPLICATION_ID,
    VERSION;
  }
  
  private final Map<FIELD, String> fieldValues = new HashMap<FIELD, String>();
  private final String url;
  private final int currentVersion;
  private final DataFetcher dataFetcher;

  public UpdateChecker(String url, int currentVersion, DataFetcher dataFetcher) {
    this.url = url;
    this.currentVersion = currentVersion;
    this.dataFetcher = dataFetcher;
  }
  
  /**
   * Reads updates from the data retreived from the provided link.
   */
  public boolean checkForUpdate() throws Exception {
    try {
      Log.d(TAG, "Looking for version at " + url);
      BufferedReader reader = dataFetcher.getData(url);
      String line = null;
      while ((line = reader.readLine()) != null) {
        Log.d(TAG, "Read line '" + line);
        String[] parts = line.split(delimiter);
        FIELD field;
        String value;
        if (parts.length == 2) {
          field = FIELD.valueOf(parts[0]);
          value = parts[1];
          fieldValues.put(field, value);
        } else {
          Log.e(TAG, "Unparseable line: '" + line + "'.");
        }
      }
      if (fieldValues.size() != FIELD.values().length) {
        Log.e(TAG, "Did not parse the correct number of field values.  Got " + fieldValues);
        return false;
      }
    } catch (MalformedURLException e) {
      Log.e(TAG, "MalformedURLException", e);
      return false;
    } catch (IOException e) {
      Log.e(TAG, "IOException", e);
      return false;
    }
    return true;
  }
  
  public String getField(FIELD field) {
    return fieldValues.get(field);
  }
  
  public boolean newVersionIsAvailable() {
    String newestVersionStr = getField(FIELD.VERSION);
    if (newestVersionStr != null) {
      try {
        int newestVersion = Integer.parseInt(newestVersionStr);
        if (newestVersion > currentVersion) {
          return true;
        }
      } catch(NumberFormatException e) {
        Log.e(TAG, "Failed to parse version code '" + newestVersionStr + "' into an integer.", e);
      }
    } else {
      Log.e(TAG, "Have not found a new version code.");
    }
    return false;
  }
}
