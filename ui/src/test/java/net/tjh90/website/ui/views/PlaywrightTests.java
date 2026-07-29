package net.tjh90.website.ui;

import com.microsoft.playwright.Browser;
import com.microsoft.playwright.Playwright;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.springframework.boot.SpringApplication;
import org.springframework.context.ConfigurableApplicationContext;

public class PlaywrightTests {

    private static ConfigurableApplicationContext context;
    private static Playwright playwright;
    protected Browser browser;

    private static final String[] args = { "--server.port=0", "--vaadin.devmode.enable=false" };

    @BeforeAll
    protected static void startApp() {
        playwright = Playwright.create();
        context = SpringApplication.run(Application.class, args);
    }

    @AfterAll
    protected static void stopApp() {
        if (context != null) {
            context.close();
        }
        if (playwright != null) {
            playwright.close();
        }
    }

    @BeforeEach
    protected void createBrowser() {
        browser = playwright.chromium().launch();
    }

    @AfterEach
    protected void closeBrowser() {
        if (browser != null) {
            browser.close();
        }
    }

    protected String baseUrl() {
        String port = context.getEnvironment().getProperty("local.server.port", String.class);
        return "http://localhost:" + port;
    }
}

