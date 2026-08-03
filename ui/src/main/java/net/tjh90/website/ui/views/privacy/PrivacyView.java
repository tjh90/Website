package net.tjh90.website.ui.views.privacy;

import java.util.List;

import com.vaadin.flow.component.Component;
import com.vaadin.flow.component.html.Div;
import com.vaadin.flow.component.html.H3;
import com.vaadin.flow.component.html.ListItem;
import com.vaadin.flow.component.html.Paragraph;
import com.vaadin.flow.component.html.UnorderedList;
import com.vaadin.flow.component.orderedlayout.HorizontalLayout;
import com.vaadin.flow.component.orderedlayout.VerticalLayout;
import com.vaadin.flow.router.Route;
import com.vaadin.flow.server.StreamResource;

import net.tjh90.website.ui.HasTitle;
import net.tjh90.website.ui.components.Icons;
import net.tjh90.website.ui.views.CssClassNames;

/// Defines the home page view.
@Route(PrivacyView.ROUTE)
public class PrivacyView extends VerticalLayout implements HasTitle {

    public static final String ROUTE = "privacy";

    public static final String TITLE = "Privacy";
    public static final String NAV_LABEL = TITLE;

    private static final String PRIVACY_TEXT =
            "This website uses essential cookies required for its operation which cannot be disabled. The cookies " +
            "include:";
    private static final String JSESSIONID_TEXT = "JSESSIONID - maintains a user session while navigating the site.";
    private static final String CSRF_TEXT =
            "csrfToken - used to protect the website against cross-site request forgery attacks.";

    public PrivacyView() {
        setPadding(true);
        setWidthFull();

        add(createContent());
    }

    private Component createContent() {
        Div privacyConainer = new Div();
        privacyConainer.setWidthFull();

        privacyConainer.add(new Paragraph(PRIVACY_TEXT));

        ListItem jSessionIdItem = new ListItem(JSESSIONID_TEXT);
        ListItem csrfItem = new ListItem(CSRF_TEXT);
        privacyConainer.add(new UnorderedList(jSessionIdItem, csrfItem));

        return privacyConainer;
    }

    @Override
    public String getTitle() {
        return TITLE;
    }
}
