package net.tjh90.website.ui.views;

import com.vaadin.flow.component.Component;
import com.vaadin.flow.component.applayout.AppLayout;
import com.vaadin.flow.component.applayout.DrawerToggle;
import com.vaadin.flow.component.checkbox.Checkbox;
import com.vaadin.flow.component.html.H1;
import com.vaadin.flow.component.orderedlayout.HorizontalLayout;
import com.vaadin.flow.component.orderedlayout.VerticalLayout;
import com.vaadin.flow.component.sidenav.SideNav;
import com.vaadin.flow.component.sidenav.SideNavItem;
import com.vaadin.flow.router.AfterNavigationEvent;
import com.vaadin.flow.router.AfterNavigationObserver;
import com.vaadin.flow.router.Layout;

import net.tjh90.website.ui.views.anascramble.AnascrambleView;
import net.tjh90.website.ui.views.home.HomeView;
import net.tjh90.website.ui.views.privacy.PrivacyView;

/// Defines the main application view elements.
@Layout
public class MainView extends AppLayout implements AfterNavigationObserver {

    private static final String DARK_MODE = "Dark mode";

    private final MainViewModel viewModel;

    private H1 title = new H1();
    private SideNavItem darkModeItem = new SideNavItem(DARK_MODE);
    private Checkbox darkModeCheckbox = new Checkbox(false);

    public MainView() {
        addToNavbar(createHeaderContent());
        addToDrawer(createSideNav());

        viewModel = new MainViewModel(this);
    }

    private Component createHeaderContent() {
        HorizontalLayout layout = new HorizontalLayout();
        layout.setWidthFull();
        layout.setClassName(CssClassNames.HEADER);

        layout.addToStart(new DrawerToggle());

        layout.addToMiddle(title);

        return layout;
    }

    private Component createSideNav() {
        // Main navigation items.
        SideNav mainNav = new SideNav();
        mainNav.setWidthFull();

        mainNav.addItem(new SideNavItem(HomeView.NAV_LABEL, HomeView.class));
        mainNav.addItem(new SideNavItem(AnascrambleView.NAV_LABEL, AnascrambleView.class));

        darkModeItem.setSuffixComponent(darkModeCheckbox);
        mainNav.addItem(darkModeItem);

        // Bottom navigation items.
        SideNav bottomNav = new SideNav();
        bottomNav.setWidthFull();
        bottomNav.addItem(new SideNavItem(PrivacyView.NAV_LABEL, PrivacyView.class));

        // Layout for side navigation.
        VerticalLayout layout = new VerticalLayout();
        layout.setSizeFull();
        layout.setPadding(false);
        layout.setSpacing(false);

        layout.add(mainNav);
        layout.expand(mainNav);
        layout.add(bottomNav);

        return layout;
    }

    @Override
    public void afterNavigation(AfterNavigationEvent event) {
        viewModel.onNavigation();
    }

    H1 getTitle() {
        return title;
    }

    Checkbox getDarkModeCheckbox() {
        return darkModeCheckbox;
    }

    SideNavItem getDarkModeItem() {
        return darkModeItem;
    }
}
