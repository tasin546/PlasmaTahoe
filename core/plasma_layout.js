// PlasmaTahoe-Engine: Plasma 6 Layout Script
// Configures Top Global Menu Panel & Bottom macOS-style Floating Dock
// Executed via qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript

(function() {
    var topHeight = __TOP_PANEL_HEIGHT__;
    var dockHeight = __DOCK_HEIGHT__;

    // 1. Cleanly remove existing panels across all screens
    try {
        var currentPanels = panels();
        for (var i = 0; i < currentPanels.length; ++i) {
            if (currentPanels[i]) {
                currentPanels[i].remove();
            }
        }
    } catch (err) {
        print("Notice during panel removal: " + err);
    }

    // Safely retrieve known widget types (knownWidgetTypes is an array in Plasma 6)
    var widgets = [];
    try {
        if (typeof knownWidgetTypes === "function") {
            widgets = knownWidgetTypes();
        } else if (Array.isArray(knownWidgetTypes)) {
            widgets = knownWidgetTypes;
        } else if (knownWidgetTypes) {
            widgets = knownWidgetTypes;
        }
    } catch (e) {
        widgets = [];
    }

    function hasWidget(id) {
        return widgets && widgets.indexOf && widgets.indexOf(id) !== -1;
    }

    // 2. Build Top Global Menu Bar (Primary Screen 0)
    var topPanel = new Panel();
    if (!topPanel) {
        print("Error: Could not allocate Top Panel containment.");
        return;
    }
    topPanel.screen = 0;
    topPanel.location = "top";
    topPanel.height = topHeight;
    topPanel.floating = false;
    topPanel.lengthMode = "fill";

    // Application Launcher / Kpple Menu
    var launcher = null;
    if (hasWidget("com.github.kppleMenu")) {
        launcher = topPanel.addWidget("com.github.kppleMenu");
    } else if (hasWidget("org.kpple.kppleMenu")) {
        launcher = topPanel.addWidget("org.kpple.kppleMenu");
    } else {
        launcher = topPanel.addWidget("org.kde.plasma.kickoff");
        if (launcher) {
            launcher.currentConfigGroup = ["General"];
            launcher.writeConfig("icon", "distributor-logo-apple");
        }
    }

    // Global Menu (Appmenu)
    var globalMenu = topPanel.addWidget("org.kde.plasma.appmenu");

    // Dynamic Panel Colorizer if installed
    if (hasWidget("luisbocanegra.panelcolorizer")) {
        topPanel.addWidget("luisbocanegra.panelcolorizer");
    }

    // Expanding Spacer
    var topSpacer = topPanel.addWidget("org.kde.plasma.panelspacer");
    if (topSpacer) {
        topSpacer.currentConfigGroup = ["General"];
        topSpacer.writeConfig("expanding", true);
    }

    // Weather widget pill if available
    if (hasWidget("com.jaxparrow07.macoswidgets.weatherpanel")) {
        topPanel.addWidget("com.jaxparrow07.macoswidgets.weatherpanel");
    }

    // System Tray
    var tray = topPanel.addWidget("org.kde.plasma.systemtray");

    // Digital Clock (Tahoe style: "MMM d  h:mm AP")
    var clock = topPanel.addWidget("org.kde.plasma.digitalclock");
    if (clock) {
        clock.currentConfigGroup = ["Appearance"];
        clock.writeConfig("customDateFormat", "MMM d  h:mm AP");
        clock.writeConfig("dateFormat", "custom");
        clock.writeConfig("showDate", true);
        clock.writeConfig("showSeconds", false);
    }

    // 3. Build Bottom Floating Dock (Primary Screen 0)
    var dock = new Panel();
    if (!dock) {
        print("Error: Could not allocate Dock containment.");
        return;
    }
    dock.screen = 0;
    dock.location = "bottom";
    dock.height = dockHeight;
    dock.floating = true;
    dock.lengthMode = "fit";
    dock.hiding = "dodgewindows";

    var tasks = dock.addWidget("org.kde.plasma.icontasks");
    if (tasks) {
        tasks.currentConfigGroup = ["General"];
        tasks.writeConfig("launchers", [
            "applications:org.kde.dolphin.desktop",
            "preferred://browser",
            "applications:org.kde.konsole.desktop",
            "applications:systemsettings.desktop"
        ]);
        tasks.writeConfig("fill", false);
    }

    // Dock Separator
    var dockSpacer = dock.addWidget("org.kde.plasma.panelspacer");
    if (dockSpacer) {
        dockSpacer.currentConfigGroup = ["General"];
        dockSpacer.writeConfig("expanding", false);
    }

    // Trash Applet
    dock.addWidget("org.kde.plasma.trash");

    print("PlasmaTahoe Layout Script Executed Successfully");
})();
