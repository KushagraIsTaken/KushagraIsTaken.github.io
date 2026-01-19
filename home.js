// Initialize Leaflet map with sample institutions; replace/add markers as needed
(function initMap() {
	const mapContainer = document.getElementById('mapid');
	if (!mapContainer || typeof L === 'undefined') return;

	const map = L.map('mapid', { scrollWheelZoom: false }).setView([20.5937, 78.9629], 4);

	L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
		attribution: '&copy; OpenStreetMap contributors'
	}).addTo(map);

	const eduIcon = L.divIcon({
		className: 'edu-icon',
		html: '<i class="fa-solid fa-graduation-cap" style="color:#2c7be5;font-size:18px;"></i>',
		iconSize: [18, 18],
		iconAnchor: [9, 9]
	});

	const workIcon = L.divIcon({
		className: 'work-icon',
		html: '<i class="fa-solid fa-briefcase" style="color:#e53e3e;font-size:18px;"></i>',
		iconSize: [18, 18],
		iconAnchor: [9, 9]
	});

	const confIcon = L.divIcon({
		className: 'conf-icon',
		html: '<i class="fa-solid fa-chalkboard-teacher" style="color:#10b981;font-size:18px;"></i>',
		iconSize: [18, 18],
		iconAnchor: [9, 9]
	});

	const institutions = [
		{ name: 'KIIT University', coords: [20.3551, 85.8193], type: 'edu' },
		{ name: 'IIIT-Delhi (MIDAS Lab)', coords: [28.5450, 77.2732], type: 'work' },
		{ name: 'Indian Statistical Institute, Kolkata', coords: [22.6492, 88.3726], type: 'work' },
		{ name: 'DRDO DYSL-AI, Bengaluru', coords: [12.9716, 77.5946], type: 'work' },
		{ name: 'Taipei Medical University', coords: [25.0262, 121.5607], type: 'work' },
		{ name: 'National Tsing Hua University', coords: [24.7956, 120.9939], type: 'work' }
	];

	const conferences = [
		{ name: 'ICEdge (IISc Bengaluru)', coords: [13.0213, 77.5670] },
		{ name: 'PReMI (IIT Delhi)', coords: [28.5450, 77.1926] },
		{ name: 'ACM Compute (IIT Ropar)', coords: [30.9686, 76.5378] },
		{ name: 'NIT Rourkela', coords: [22.2534, 84.9049] },
		{ name: 'MANIT Bhopal', coords: [23.2134, 77.4140] },
		{ name: 'Manipal University Jaipur', coords: [26.8428, 75.5650] }
	];

	institutions.forEach(inst => {
		const icon = inst.type === 'edu' ? eduIcon : workIcon;
		L.marker(inst.coords, { icon }).addTo(map).bindPopup(`<strong>${inst.name}</strong>`);
	});

	conferences.forEach(c => {
		L.marker(c.coords, { icon: confIcon }).addTo(map).bindPopup(`<strong>${c.name}</strong>`);
	});
})();

// Optional: Fetch live Google Scholar citations (requires a proxy API because Scholar blocks CORS)
(function initScholarCitations() {
	const el = document.getElementById('scholar-live');
	const valueEl = document.getElementById('scholar-citations');
	if (!el || !valueEl) return;

	// Hide by default; show only on success
	el.hidden = true;

	// Replace with your own backend endpoint that scrapes Scholar server-side
	const endpoint = '';
	if (!endpoint) return; // do nothing until configured

	fetch(endpoint, { method: 'GET' })
		.then(resp => resp.json())
		.then(data => {
			if (data && typeof data.citations === 'number') {
				valueEl.textContent = String(data.citations);
				el.hidden = false;
			}
		})
		.catch(() => { });
})();

// Selected publications (top N) injected on the homepage
(function initSelectedPublications() {
	const container = document.getElementById('selected-publications-container');
	if (!container || !Array.isArray(window.publications)) return;

	// Ensure specific featured papers appear first
	const featuredTitles = new Set([
		'IndiSegNet: Real-time semantic segmentation for unstructured road scenes in intelligent transportation systems',
		'Artificial Intelligence in Personalized Nutrition and Food Manufacturing: A Comprehensive Review of Methods, Applications, and Future Directions',
		'AI-Driven Transformation in Food Manufacturing: A Pathway to Sustainable Efficiency and Quality Assurance',
		'Neural Orchestration for Multi-Agent Systems: A Deep Learning Framework for Optimal Agent Selection in Multi-Domain Task Environments'
	]);

	const featured = window.publications.filter(p => featuredTitles.has(p.title));
	const rest = window.publications.filter(p => !featuredTitles.has(p.title));
	const selected = [...featured, ...rest].slice(0, 5);

	selected.forEach(pub => {
		const wrapper = document.createElement('div');
		wrapper.className = 'selected-publication';

		const title = pub.title || 'Untitled';
		const authors = pub.authors || '';
		const venue = [pub.journal, pub.booktitle].filter(Boolean)[0] || '';
		const year = pub.year || '';

		const url = pub.url || (title ? `https://scholar.google.com/scholar?q=${encodeURIComponent(title)}` : '');

		const a = document.createElement('a');
		a.href = url;
		a.target = '_blank';
		a.rel = 'noopener';
		a.textContent = title;

		const meta = document.createElement('div');
		meta.textContent = [authors, venue, year].filter(Boolean).join(' · ');

		wrapper.appendChild(a);
		wrapper.appendChild(meta);
		container.appendChild(wrapper);
	});
})();
