// PlasmaTahoe-Engine: Plasma 6 Layout Script
// Configures Top Global Menu Panel & Bottom macOS-style Floating Dock
// Executed via qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript

(function() {
    var topHeight = __TOP_PANEL_HEIGHT__;
    var dockHeight = __DOCK_HEIGHT__;

    // 1. Cleanly remove existing panels
    var currentPanels = panels();
    for (var i = 0; i < currentPanels.length; ++i) {
        currentPanels[i].remove();
    }

    // 2. Build Top Global Menu Bar
    var topPanel = new Panel();
    topPanel.location = "top";
    topPanel.height = topHeight;
    topPanel.floating = false;
    topPanel.lengthMode = "fill";

    // Application Launcher / Kpple Menu
    var launcher;
    var widgets = knownWidgetTypes();
    if (widgets.indexOf("com.github.kppleMenu") !== -1) {
        launcher = topPanel.addWidget("com.github.kppleMenu");
    } else if (widgets.indexOf("org.kpple.kppleMenu") !== -1) {
        launcher = topPanel.addWidget("org.kpple.kppleMenu");
    } else {
        launcher = topPanel.addWidget("org.kde.plasma.kickoff");
        launcher.currentConfigGroup = ["General"];
        launcher.writeConfig("icon", "distributor-logo-apple");
    }

    // Global Menu (Appmenu)
    var globalMenu = topPanel.addWidget("org.kde.plasma.appmenu");

    // Dynamic Panel Colorizer if installed
    if (widgets.indexOf("luisbocanegra.panelcolorizer") !== -1) {
        topPanel.addWidget("luisbocanegra.panelcolorizer");
    }

    // Expanding Spacer
    var topSpacer = topPanel.addWidget("org.kde.plasma.panelspacer");
    topSpacer.currentConfigGroup = ["General"];
    topSpacer.writeConfig("expanding", true);

    // Weather widget pill if available
    if (widgets.indexOf("com.jaxparrow07.macoswidgets.weatherpanel") !== -1) {
        topPanel.addWidget("com.jaxparrow07.macoswidgets.weatherpanel");
    }

    // System Tray
    var tray = topPanel.addWidget("org.kde.plasma.systemtray");

    // Digital Clock (Tahoe style: "MMM d  h:mm AP")
    var clock = topPanel.addWidget("org.kde.plasma.digitalclock");
    clock.currentConfigGroup = ["Appearance"];
    clock.writeConfig("customDateFormat", "MMM d  h:mm AP");
    clock.writeConfig("dateFormat", "custom");
    clock.writeConfig("showDate", true);
    clock.writeConfig("showSeconds", false);

    // 3. Build Bottom Floating Dock
    var dock = new Panel();
    dock.location = "bottom";
    dock.height = dockHeight;
    dock.floating = true;
    dock.lengthMode = "fit";
    dock.hiding = "dodgewindows";

    var tasks = dock.addWidget("org.kde.plasma.icontasks");
    tasks.currentConfigGroup = ["General"];
    tasks.writeConfig("launchers", [
        "applications:org.kde.dolphin.desktop",
        "preferred://browser",
        "applications:org.kde.konsole.desktop",
        "applications:systemsettings.desktop"
    ]);
    tasks.writeConfig("fill", false);

    // Dock Separator
    var dockSpacer = dock.addWidget("org.kde.plasma.panelspacer");
    dockSpacer.currentConfigGroup = ["General"];
    dockSpacer.writeConfig("expanding", false);

    // Trash
    dock.addWidget("org.kde.plasma.trash");

    print("PlasmaTahoe Layout Script Executed Successfully");
})();
