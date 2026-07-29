package net.tjh90.website.ui;

import com.microsoft.playwright.Browser;
import com.microsoft.playwright.Page;
import com.microsoft.playwright.Playwright;
import com.microsoft.playwright.Response;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.boot.SpringApplication;
import org.springframework.context.ConfigurableApplicationContext;

import static org.junit.jupiter.api.Assertions.assertTrue;

class MainViewTests {

    private static ConfigurableApplicationContext context;
    private static Playwright playwright;
    private Browser browser;

    @BeforeAll
    protected static void startApp() {
        playwright = Playwright.create();
        context = SpringApplication.run(Application.class,
            "--server.port=0",
            "--vaadin.devmode.enabled=false");
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

    private String baseUrl() {
        String port = context.getEnvironment().getProperty("local.server.port", String.class);
        return "http://localhost:" + port;
    }

    @Test
    protected void homePageLoadsSuccessfully() {
        Page page = browser.newPage();
        Response response = page.navigate(baseUrl() + "/");
        assertTrue(response.ok());
    }

    @ParameterizedTest
    @ValueSource(strings = {"/anascramble", "/privacy"})
    protected void anascramblePageHasExpectedRoute(String route) {
        Page page = browser.newPage();
        page.navigate(baseUrl() + route);
        assertTrue(page.url().endsWith(route));
    }
}
