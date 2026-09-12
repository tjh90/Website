package net.tjh90.website.ui;

import com.vaadin.flow.component.dependency.CssImport;
import com.vaadin.flow.component.page.AppShellConfigurator;
import com.vaadin.flow.server.AppShellSettings;
import com.vaadin.flow.theme.Theme;
import net.tjh90.website.ui.views.home.HomeView;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/// Main application class.
@SpringBootApplication
@Theme(value = "default")
@CssImport("./fontawesome/css/all.css")
public class Application implements AppShellConfigurator {

  private static final String FAVICON = "favicon.ico";
  private static final String FAVICON_SIZE = "256x256";

  public static void main(String[] args) {
    SpringApplication.run(Application.class, args);
  }

  @Override
  public void configurePage(final AppShellSettings settings) {
    settings.setPageTitle(HomeView.TITLE);
    settings.addFavIcon(FAVICON, FAVICON, FAVICON_SIZE);
  }
}
