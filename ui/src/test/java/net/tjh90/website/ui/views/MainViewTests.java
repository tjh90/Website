package net.tjh90.website.ui.views;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.microsoft.playwright.Browser;
import com.microsoft.playwright.Locator;
import com.microsoft.playwright.Page;
import com.microsoft.playwright.Response;
import com.microsoft.playwright.options.AriaRole;
import com.microsoft.playwright.options.LoadState;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.ValueSource;

import net.tjh90.website.ui.PlaywrightTests;

class MainViewTests extends PlaywrightTests {

    private static final String APP_LAYOUT = "vaadin-app-layout";
    private static final String CHECKBOX = "vaadin-side-nav-item vaadin-checkbox";

    @Test
    protected void homePageLoadsSuccessfully() {
        Page page = browser.newPage();
        Response response = page.navigate(baseUrl() + "/");
        assertTrue(response.ok());
    }

    @ParameterizedTest
    @ValueSource(strings = {"/anascramble", "/privacy"})
    protected void pagesHaveExpectedRoutes(String route) {
        Page page = browser.newPage();
        page.navigate(baseUrl() + route);
        assertTrue(page.url().endsWith(route));
    }

    @ParameterizedTest
    @CsvSource({
        "Home, /",
        "Anascramble, /anascramble",
        "Privacy, /privacy"
    })
    protected void clickingNavItemNavigatesToCorrectPage(String navLabel, String expectedRoute) {
        Page page = browser.newPage();
        page.navigate(baseUrl() + "/");
        page.waitForLoadState(LoadState.DOMCONTENTLOADED);

        page.locator(APP_LAYOUT).getByRole(AriaRole.BUTTON).first().click();
        page.getByRole(AriaRole.LINK, new Page.GetByRoleOptions().setName(navLabel)).first().click();
        page.waitForLoadState(LoadState.NETWORKIDLE);

        assertTrue(page.url().endsWith(expectedRoute));
    }

    @Test
    protected void darkModeToggleViaMenuItemClick() {
        Page page = browser.newPage();
        page.navigate(baseUrl() + "/");
        page.waitForLoadState(LoadState.DOMCONTENTLOADED);

        assertFalse(isDarkThemeActive(page));
        assertTrue(isBackgroundLight(page));

        openDrawer(page);

        page.click("text=" + MainView.DARK_MODE_TEXT);
        page.waitForTimeout(2000);
        assertTrue(isDarkThemeActive(page), "Dark theme should be active after clicking menu item");
        assertFalse(isBackgroundLight(page));

        page.click("text=" + MainView.DARK_MODE_TEXT);
        page.waitForTimeout(2000);
        assertFalse(isDarkThemeActive(page), "Dark theme should be inactive after clicking menu item again");
        assertTrue(isBackgroundLight(page));
    }

    @Test
    protected void darkModeToggleViaCheckboxClick() {
        Page page = browser.newPage();
        page.navigate(baseUrl() + "/");
        page.waitForLoadState(LoadState.DOMCONTENTLOADED);

        assertFalse(isDarkThemeActive(page));
        assertTrue(isBackgroundLight(page));

        openDrawer(page);

        page.click(CHECKBOX);
        page.waitForTimeout(2000);
        assertTrue(isDarkThemeActive(page), "Dark theme should be active after clicking checkbox");
        assertFalse(isBackgroundLight(page));

        page.click(CHECKBOX);
        page.waitForTimeout(2000);
        assertFalse(isDarkThemeActive(page), "Dark theme should be inactive after clicking checkbox again");
        assertTrue(isBackgroundLight(page));
    }

    @Test
    protected void drawerClosesAfterNavigation() {
        Page page = browser.newPage();
        page.navigate(baseUrl() + "/");
        page.waitForLoadState(LoadState.DOMCONTENTLOADED);

        openDrawer(page);
        assertTrue(isDrawerOpened(page));

        page.getByRole(AriaRole.LINK, new Page.GetByRoleOptions().setName("Privacy")).first().click();
        page.waitForLoadState(LoadState.NETWORKIDLE);

        assertFalse(isDrawerOpened(page));
    }

    @Test
    protected void unknownRouteReturnsOkResponse() {
        Page page = browser.newPage();
        Response response = page.navigate(baseUrl() + "/this-route-does-not-exist");
        assertTrue(response.ok());
    }

    @Test
    protected void mobileViewportNavigationWorks() {
        Page page = browser.newPage(new Browser.NewPageOptions().setViewportSize(375, 812));
        page.navigate(baseUrl() + "/");
        page.waitForLoadState(LoadState.DOMCONTENTLOADED);

        page.locator(APP_LAYOUT).getByRole(AriaRole.BUTTON).first().click();
        page.waitForTimeout(300);
        assertTrue(isDrawerOpened(page));

        page.getByRole(AriaRole.LINK, new Page.GetByRoleOptions().setName("Privacy")).first().click();
        page.waitForLoadState(LoadState.NETWORKIDLE);

        assertTrue(page.url().endsWith("/privacy"));
        assertFalse(isDrawerOpened(page));
    }

    private void openDrawer(Page page) {
        page.locator(APP_LAYOUT).getByRole(AriaRole.BUTTON).first().click();
        page.waitForTimeout(300);
        assertTrue(isDrawerOpened(page));
    }

    private static boolean isDrawerOpened(Page page) {
        return Boolean.TRUE.equals(page.evaluate(
            "document.querySelector('vaadin-app-layout')?.drawerOpened"));
    }

    private static boolean isDarkThemeActive(Page page) {
        return Boolean.TRUE.equals(page.evaluate(
            "document.body.getAttribute('theme')?.includes('dark') ?? false"));
    }

    private static boolean isBackgroundLight(Page page) {
        return Boolean.TRUE.equals(page.evaluate(
            "(() => { const c = getComputedStyle(document.body).backgroundColor.trim();" +
            "if (!c || c === 'transparent' || c === 'rgba(0, 0, 0, 0)') return true;" +
            "const [r, g, b] = c.match(/\\d+(?:\\.\\d+)?/g).map(Number);" +
            "return (r + g + b) / 3 > 128; })()"));
    }
}
