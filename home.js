// Institutions & collaborations map (Leaflet)
(function initMap() {
	const mapContainer = document.getElementById('mapid');
	if (!mapContainer) return;
	if (typeof L === 'undefined') {
		mapContainer.classList.add('map-error');
		mapContainer.innerHTML = '<p>The map could not load. Please check your connection and refresh.</p>';
		return;
	}

	const isTouch = window.matchMedia('(pointer: coarse)').matches;

	const map = L.map(mapContainer, {
		scrollWheelZoom: false,
		dragging: !isTouch,
		tap: false,
		zoomSnap: 0.25,
		worldCopyJump: true,
		minZoom: 2
	});

	// OpenStreetMap tiles (dark mode is handled with a CSS filter in style.css)
	L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
		attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
		maxZoom: 19
	}).addTo(map);

	const pin = (type, icon) => L.divIcon({
		className: '',
		html: `<span class="map-pin ${type}"><i class="fa-solid ${icon}"></i></span>`,
		iconSize: [30, 30],
		iconAnchor: [15, 15],
		popupAnchor: [0, -14]
	});

	const icons = {
		edu: pin('edu', 'fa-graduation-cap'),
		work: pin('work', 'fa-briefcase'),
		conf: pin('conf', 'fa-chalkboard-user')
	};

	const labels = { edu: 'Education', work: 'Research / work', conf: 'Conference / school' };

	const places = [
		{ name: 'KIIT University, Bhubaneswar', coords: [20.3551, 85.8193], type: 'edu', region: 'india' },
		{ name: 'Åbo Akademi University, Turku', coords: [60.4510, 22.2776], type: 'edu', region: 'europe' },
		{ name: 'University of Cambridge (ELLIS Summer School)', coords: [52.2043, 0.1149], type: 'conf', region: 'europe' },
		{ name: 'IIIT-Delhi (MIDAS Lab)', coords: [28.5450, 77.2732], type: 'work', region: 'india' },
		{ name: 'Indian Statistical Institute, Kolkata', coords: [22.6492, 88.3726], type: 'work', region: 'india' },
		{ name: 'DRDO DYSL-AI, Bengaluru', coords: [12.9716, 77.5946], type: 'work', region: 'india' },
		{ name: 'Taipei Medical University', coords: [25.0262, 121.5607], type: 'work', region: 'taiwan' },
		{ name: 'National Tsing Hua University, Hsinchu', coords: [24.7956, 120.9939], type: 'work', region: 'taiwan' },
		{ name: 'ICEdge (IISc Bengaluru)', coords: [13.0213, 77.5670], type: 'conf', region: 'india' },
		{ name: 'PReMI (IIT Delhi)', coords: [28.5450, 77.1926], type: 'conf', region: 'india' },
		{ name: 'ACM Compute (IIT Ropar)', coords: [30.9686, 76.5378], type: 'conf', region: 'india' },
		{ name: 'NIT Rourkela', coords: [22.2534, 84.9049], type: 'conf', region: 'india' },
		{ name: 'MANIT Bhopal', coords: [23.2134, 77.4140], type: 'conf', region: 'india' },
		{ name: 'Manipal University Jaipur', coords: [26.8428, 75.5650], type: 'conf', region: 'india' },
		{ name: 'IIIT Hyderabad (CVIT Summer School)', coords: [17.4455, 78.3489], type: 'conf', region: 'india' }
	];

	const markers = places.map(p => {
		const m = L.marker(p.coords, { icon: icons[p.type], title: p.name, riseOnHover: true })
			.addTo(map)
			.bindPopup(`<strong>${p.name}</strong><br><span class="map-popup-type">${labels[p.type]}</span>`);
		m.region = p.region;
		return m;
	});

	const boundsFor = (region) => L.featureGroup(region === 'all' ? markers : markers.filter(m => m.region === region)).getBounds();
	const pad = () => (mapContainer.offsetWidth < 500 ? [24, 24] : [50, 50]);
	const show = (region, animate) => {
		const b = boundsFor(region);
		const maxZoom = region === 'taiwan' ? 8 : region === 'europe' ? 5 : 6;
		map.flyToBounds ? (animate ? map.flyToBounds(b, { padding: pad(), maxZoom, duration: 0.8 }) : map.fitBounds(b, { padding: pad(), maxZoom }))
			: map.fitBounds(b, { padding: pad(), maxZoom });
	};

	// Region buttons
	let current = 'all';
	const buttons = document.querySelectorAll('.map-region-btn');
	buttons.forEach(btn => {
		btn.addEventListener('click', () => {
			current = btn.dataset.region;
			buttons.forEach(b => b.setAttribute('aria-pressed', String(b === btn)));
			show(current, true);
		});
	});

	show(current, false);

	// Keep the map sized correctly when its section animates in or the window resizes
	const refresh = () => { map.invalidateSize(); };
	window.addEventListener('resize', () => { clearTimeout(refresh.t); refresh.t = setTimeout(() => { refresh(); show(current, false); }, 200); });
	if ('IntersectionObserver' in window) {
		new IntersectionObserver((entries, obs) => {
			if (entries[0].isIntersecting) { setTimeout(refresh, 650); obs.disconnect(); }
		}).observe(mapContainer);
	}

	// Touch devices: one finger scrolls the page until the user taps the map to explore it
	if (isTouch) {
		const hint = document.createElement('button');
		hint.type = 'button';
		hint.className = 'map-touch-hint';
		hint.innerHTML = '<i class="fa-solid fa-hand-pointer"></i> Tap to explore the map';
		mapContainer.appendChild(hint);
		L.DomEvent.disableClickPropagation(hint);
		hint.addEventListener('click', () => {
			map.dragging.enable();
			map.touchZoom.enable();
			hint.remove();
		});
	}
})();

// Selected publications (top N) injected on the homepage
(function initSelectedPublications() {
	const container = document.getElementById('selected-publications-container');
	if (!container || !Array.isArray(window.publications)) return;

	// Keys from publications.bib to show first on the homepage
	const featuredKeys = [
		'agrawal2026translating',
		'agrawal2026token',
		'chakraborty2026indisegnet',
		'agrawal2025artificial',
		'agrawal2025ai'
	];
	const featured = featuredKeys.map(k => window.publications.find(p => p.key === k)).filter(Boolean);
	const rest = window.publications.filter(p => !featuredKeys.includes(p.key));
	const selected = [...featured, ...rest].slice(0, 5);

	selected.forEach(pub => {
		const wrapper = document.createElement('article');
		wrapper.className = 'selected-publication';

		const title = pub.title || 'Untitled';
		const url = pub.url || `publications.html#${pub.key}`;

		const a = document.createElement('a');
		a.href = url;
		if (pub.url) { a.target = '_blank'; a.rel = 'noopener'; }
		a.textContent = title;

		const authors = document.createElement('div');
		authors.className = 'pub-meta';
		authors.textContent = pub.authors || '';

		const venue = document.createElement('div');
		venue.className = 'pub-meta';
		if (pub.journal) {
			const em = document.createElement('em');
			em.textContent = pub.journal;
			venue.appendChild(em);
		}
		const tail = [pub.publisher, pub.year].filter(Boolean).join(', ');
		if (tail) venue.appendChild(document.createTextNode((pub.journal ? ', ' : '') + tail));

		wrapper.append(a, authors, venue);
		container.appendChild(wrapper);
	});
})();
