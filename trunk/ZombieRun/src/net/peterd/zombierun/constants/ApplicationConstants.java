package net.peterd.zombierun.constants;

public class ApplicationConstants {

  private static final boolean developing = true;
  
  private static final String develMapsApiKey = "0gTCqChu4DUp2u2dMhUspP8EJlh8YeMUjO3FYqQ";

  // This is not filled in because the key could be stolen from the public
  // source code repository.
  private static final String releaseMapsApiKey = "--- filled in by the project manager before each release ---";

  public static String getMapsApiKey() {
    return developing ? develMapsApiKey : releaseMapsApiKey;
  }
  
  public static boolean loggingEnabled() {
    return developing;
  }
  
  // The current version code must be incremented when releasing a new version.
  // The version code MUST be kept in sync with the version code stored in AndroidManifest.xml
  public static final int currentVersionCode = 7;
  public static final String applicationVersionCheckUrl = "http://www.zrli.org/zombierun/version";
  public static final String aboutUrl = "http://www.zrli.org/zombierun/";
  
  public static final boolean multiplayerEnabled = false;
}
