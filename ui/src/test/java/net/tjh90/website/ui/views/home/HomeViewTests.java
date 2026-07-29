package net.tjh90.website.ui.views.home;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.microsoft.playwright.Locator;
import com.microsoft.playwright.Page;
import com.microsoft.playwright.options.LoadState;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.stream.Stream;

import net.tjh90.website.ui.PlaywrightTests;

class HomeViewTests extends PlaywrightTests {

    private static final int NAVIGATION_TIMEOUT = 15000;
    private static final HttpClient HTTP_CLIENT = HttpClient.newBuilder()
        .followRedirects(HttpClient.Redirect.NORMAL)
        .build();

    private static Stream<Arguments> linkProvider() {
        return Stream.of(
            Arguments.of(HomeView.GITHUB_TEXT, HomeView.GITHUB_LINK),
            Arguments.of(HomeView.PHD_THESIS_TEXT, HomeView.PHD_THESIS_LINK),
            Arguments.of(HomeView.PAPER_TEXT, HomeView.PAPER_LINK)
        );
    }

    @ParameterizedTest
    @MethodSource("linkProvider")
    protected void linksInDomHaveExpectedHref(String linkText, String expectedHref) {
        Page page = browser.newPage();
        page.navigate(baseUrl() + "/");
        page.waitForLoadState(LoadState.DOMCONTENTLOADED);

        // Get the element with matching link text.
        Locator link = page.locator("a").and(page.getByText(linkText));
        assertNotNull(link);

        // Check link points to the correct place.
        String actualHref = link.getAttribute("href");
        assertEquals(expectedHref, actualHref);
    }

    @ParameterizedTest
    @MethodSource("linkProvider")
    protected void linksAreValid(String linkText, String url) throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(url))
            .method("HEAD", HttpRequest.BodyPublishers.noBody())
            .timeout(Duration.ofMillis(NAVIGATION_TIMEOUT))
            .build();

        HttpResponse<Void> response = HTTP_CLIENT.send(request,
            HttpResponse.BodyHandlers.discarding());

        int status = response.statusCode();
        assertTrue(status >= 200 && status < 300, () -> "Link: " + url + " returned: " + status);
    }

    @ParameterizedTest
    @MethodSource("linkProvider")
    protected void clickingLinkNavigatesToValidDestination(String linkText, String expectedUrl) {
        Page page = browser.newPage();
        page.navigate(baseUrl() + "/");

        Locator link = page.locator("a").and(page.getByText(linkText));

        Page newPage = page.waitForPopup(() -> link.click());
        newPage.waitForLoadState(LoadState.DOMCONTENTLOADED);

        String finalUrl = newPage.url();
        assertTrue(finalUrl.startsWith(expectedUrl.replace("www.", "")) || finalUrl.startsWith(expectedUrl),
            () -> "Clicking \"" + linkText + "\" expected URL:" + expectedUrl + " but got: " + finalUrl);
    }
}
