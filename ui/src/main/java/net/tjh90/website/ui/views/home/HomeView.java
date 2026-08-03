package net.tjh90.website.ui.views.home;

import java.util.List;

import com.vaadin.flow.component.Component;
import com.vaadin.flow.component.Text;
import com.vaadin.flow.component.html.Anchor;
import com.vaadin.flow.component.html.AnchorTarget;
import com.vaadin.flow.component.html.H3;
import com.vaadin.flow.component.html.Image;
import com.vaadin.flow.component.orderedlayout.HorizontalLayout;
import com.vaadin.flow.component.orderedlayout.VerticalLayout;
import com.vaadin.flow.router.Route;
import com.vaadin.flow.server.streams.DownloadHandler;

import net.tjh90.website.ui.HasTitle;
import net.tjh90.website.ui.components.Icons;
import net.tjh90.website.ui.views.CssClassNames;

/// Defines the home page view.
@Route(HomeView.ROUTE)
public class HomeView extends HorizontalLayout implements HasTitle {

    public static final String ROUTE = "";

    public static final String NAV_LABEL = "Home";
    public static final String TITLE = "Tim's Page";

    static final String GITHUB_LINK = "https://www.github.com/tjh90";
    static final String GITHUB_TEXT = "GitHub";
    static final String PHD_THESIS_LINK = "https://eprints.soton.ac.uk/404274/";
    static final String PHD_THESIS_TEXT = "PhD Thesis";
    static final String PAPER_LINK = "https://ieeexplore.ieee.org/document/7029130";
    static final String PAPER_TEXT = "Paper";

    private static final String LINKS_TEXT = "Links:";

    private static final String IMG = "sisley.jpg";
    private static final String IMG_ALT_TEXT = "Sisley - Lady's Cove (1897)";

    public HomeView() {
        setPadding(true);
        setWidthFull();

        addToStart(createLinksSection());
        addToEnd(createImageSection());
    }

    private static Component createLinksSection() {
        H3 linksText = new H3(LINKS_TEXT);

        VerticalLayout layout = new VerticalLayout(linksText);
        layout.add(createLinks());

        return layout;
    }

    private static Component createImageSection() {
        DownloadHandler imgDownloadHandler = DownloadHandler.forClassResource(HomeView.class, IMG);
        return new Image(imgDownloadHandler, IMG_ALT_TEXT);
    }

    private static List<Component> createLinks() {
        Anchor githubLink = new Anchor(GITHUB_LINK, new Text(GITHUB_TEXT));
        HorizontalLayout githubLayout = new HorizontalLayout(Icons.GITHUB.create(), githubLink);

        Anchor phdThesisLink = new Anchor(PHD_THESIS_LINK, new Text(PHD_THESIS_TEXT));
        HorizontalLayout phdThesisLayout = new HorizontalLayout(Icons.PHD_THESIS.create(), phdThesisLink);

        Anchor paperLink = new Anchor(PAPER_LINK, new Text(PAPER_TEXT));
        HorizontalLayout paperLayout = new HorizontalLayout(Icons.PAPER.create(), paperLink);

        List<Anchor> links = List.of(githubLink, phdThesisLink, paperLink);
        for (Anchor link : links) {
            link.setTarget(AnchorTarget.BLANK);
        }

        List<HorizontalLayout> layouts = List.of(githubLayout, phdThesisLayout, paperLayout);
        for (HorizontalLayout layout : layouts) {
            layout.setClassName(CssClassNames.LINK);
            layout.setDefaultVerticalComponentAlignment(Alignment.CENTER);
        }

        return layouts.stream().map(l -> (Component) l).toList();
    }

    @Override
    public String getTitle() {
        return TITLE;
    }
}
